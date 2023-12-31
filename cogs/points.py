import aiosqlite
import discord
from discord.ext import commands, tasks

import config as cfg

msg_id = ['1151871558504153230']

class LBV(discord.ui.View):
    def __init__(self, db):
        self.db = db
        super().__init__(timeout=None)

    @discord.ui.button(label="Points", style=discord.ButtonStyle.green, custom_id="points:green:points")
    async def points(self, interaction, button):
        artists = interaction.guild.get_role(cfg.ARTISTS)
        if artists not in interaction.user.roles:
            return await interaction.response.send_message(
                f"{interaction.user.mention} This command is only for designers of this server.", ephemeral=True)
        cursor = await self.db.cursor()
        await cursor.execute("SELECT user_id FROM points ORDER BY points DESC")
        res = await cursor.fetchall()
        await cursor.execute("SELECT points FROM points ORDER BY points DESC")
        points = await cursor.fetchall()

        if len(points) >= 5 and len(res) >= 5:
            top = points[0]
            sec = points[1]
            third = points[2]
            fourth = points[3]
            fifth = points[4]
            top_res = res[0]
            sec_res = res[1]
            third_res = res[2]
            fourth_res = res[3]
            fifth_res = res[4]
            embed = discord.Embed(title="Points",
                                  description=f"1) <@{top_res[0]}> - {top[0]}\n2) <@{sec_res[0]}> - {sec[0]}\n3) <@{third_res[0]}> - {third[0]}\n4) <@{fourth_res[0]}> - {fourth[0]}\n5) <@{fifth_res[0]}> - {fifth[0]}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Not enough data for the leaderboard.", ephemeral=True)

class PointsCog(commands.Cog):
    """COG which handles with the point system of artists"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.bot.loop.create_task(self.connect_database())

    async def connect_database(self):
        self.db = await aiosqlite.connect('/home/ubuntu/graphics-code-bott/db/points.db')

    @commands.command(name="points")
    async def points_command(self, ctx, member: discord.Member = None):
        self.ctx = ctx

        artists = ctx.guild.get_role(cfg.ARTISTS)
        if artists not in ctx.author.roles:
            return
        member = member or ctx.author
        cursor = await self.db.cursor()
        await cursor.execute("SELECT * FROM points WHERE user_id = ?", (member.id,))
        res = await cursor.fetchone()
        
        if res is None:
            await cursor.execute("INSERT INTO points(user_id, points) VALUES(?,?)", (member.id, 0))
            await self.db.commit()
            res = (member.id, 0)  # Set a default value for res
        
        e = discord.Embed(title="Points",
                        description=f"**Displaying FX points of {member.mention}**\n\nPoints:- `{res[1]}`",
                        color=cfg.CLR)
        await ctx.send(embed=e)


    @commands.command(name="leaderboard", aliases=["lb", "pointslb", "plb"])
    async def leaderboard_command(self, ctx):
        artists = ctx.guild.get_role(cfg.ARTISTS)
        
        if artists not in ctx.author.roles:
            return
        
        cursor = await self.db.cursor()
        
        await cursor.execute("SELECT user_id FROM points ORDER BY points DESC")
        res = await cursor.fetchall()
        
        # Check if there are at least 5 results before accessing elements
        if len(res) >= 5:
            top = res[0]
            sec = res[1]
            third = res[2]
            fourth = res[3]
            fifth = res[4]
        else:
            # Handle the case where there are not enough results
            top = sec = third = fourth = fifth = None
        
        embed = discord.Embed(title="Leaderboard",
                            description=f"Expected designer of the month:- <@{top[0] if top else 'N/A'}>\n\n```Top 5```\n\n1)<@{top[0] if top else 'N/A'}>\n2)<@{sec[0] if sec else 'N/A'}>\n3)<@{third[0] if third else 'N/A'}>\n4)<@{fourth[0] if fourth else 'N/A'}>\n5)<@{fifth[0] if fifth else 'N/A'}>",
                            color=cfg.CLR)
        
        embed.set_image(url="https://media.discordapp.net/attachments/1150321238997205002/1150321298560536586/leaderboardgif.gif")
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url)
        
        await cursor.execute("SELECT points FROM points ORDER BY points DESC")
        points = await cursor.fetchall()
        
        msg = await ctx.send(embed=embed, view=LBV(self.db))
        
        if ctx.channel.id == 1150284418947219586:
            try:
                msg_id.clear()
            except:
                pass
            msg_id.append(msg.id)


    @commands.command(name="addp")
    @commands.has_permissions(administrator=True)
    async def add_points_command(self, ctx, member: discord.Member, *, points: int):
        cursor = await self.db.cursor()
        await cursor.execute("SELECT * FROM points WHERE user_id = ?", (member.id,))
        res = await cursor.fetchone()
        points_final = res[1] + points
        if res == None:
            return await ctx.send(f"{member.mention} does not have any points.")
        elif res:
            await cursor.execute("UPDATE points SET points = ? WHERE user_id = ?", (points_final, member.id))
            await self.db.commit()

        embed = discord.Embed(description=f"```Points added```\n**{points} points were added to {member.mention}**",
                              color=cfg.CLR)
        await ctx.send(embed=embed)

    @commands.command(name="delp")
    @commands.has_permissions(administrator=True)
    async def remove_points_command(self, ctx, member: discord.Member, *, points: int):
        cursor = await self.db.cursor()
        await cursor.execute("SELECT * FROM points WHERE user_id = ?", (member.id,))
        res = await cursor.fetchone()
        points_final = res[1] - points
        if res == None:
            return await ctx.send(f"{member.mention} does not have any points.")
        elif res:
            await cursor.execute("UPDATE points SET points = ? WHERE user_id = ?", (points_final, member.id))
            await self.db.commit()

        embed = discord.Embed(description=f"```Points removed```\n**{points} points were removed from {member.mention}**",
                              color=cfg.CLR)
        await ctx.send(embed=embed)

    @tasks.loop(hours=2.0)
    async def update_leaderboard(self):
        cursor = await self.db.cursor()
        message_id = msg_id[0]  # Make sure msg_id is correctly defined and contains the message ID

        await cursor.execute("SELECT user_id FROM points ORDER BY points DESC")
        res = await cursor.fetchall()

        if len(res) >= 5:
            top = res[0]
            sec = res[1]
            third = res[2]
            fourth = res[3]
            fifth = res[4]

            embed = discord.Embed(title="Leaderboard",
                                description=f"Expected designer of the month:- <@{top[0]}>\n\n```Top 5```\n\n1)<@{top[0]}>\n2)<@{sec[0]}>\n3)<@{third[0]}>\n4)<@{fourth[0]}>\n5)<@{fifth[0]}>",
                                color=cfg.CLR)

            embed.set_image(
                url="https://media.discordapp.net/attachments/1150321238997205002/1150321298560536586/leaderboardgif.gif")

            await cursor.execute("SELECT points FROM points ORDER BY points DESC")
            points = await cursor.fetchall()

            msg = await self.ctx.fetch_message(message_id)
            await msg.edit(embed=embed, view=LBV(points, res))
        else:
            print("Not enough data for the leaderboard.")

async def setup(bot):
    await bot.add_cog(PointsCog(bot))
