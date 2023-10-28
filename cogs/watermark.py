import discord
from discord.ext import commands
from PIL import Image
import requests
from io import BytesIO

class Watermark(commands.Cog):
    """
    Cog for handling watermark related requests.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def watermark(self, ctx, image_link: str = None):
        """
        Apply a watermark to an uploaded image or an image from a provided link.

        Parameters:
        - ctx (commands.Context): The context of the command invocation.
        - image_link (str): Optional. The link to an image for watermarking.

        The command checks for uploaded images or provided links. It fetches the image and applies a watermark.
        """
        # Check if an image link or an attachment is provided
        if not image_link and len(ctx.message.attachments) == 0:
            await ctx.send("Please upload an image or provide an image link.")
            return

        # If an image link is provided, fetch the image using the link
        if image_link:
            response = requests.get(image_link)
            if response.status_code != 200:
                await ctx.send("Failed to fetch the image from the provided link.")
                return
            image_data = BytesIO(response.content)
        else:
            # If an image is uploaded, retrieve the attachment
            attachment = ctx.message.attachments[0]
            image_data = BytesIO(await attachment.read())

        try:
            # Open the image and the watermark
            image = Image.open(image_data)
            watermark = Image.open("assets/wm.png")

            # Adjust the watermark size based on the image
            input_width, input_height = image.size
            watermark = watermark.resize((input_width // 2, input_height // 2))

            # Create a transparent layer to paste the watermark onto
            watermark_width, watermark_height = watermark.size
            transparent = Image.new('RGBA', (input_width, input_height), (0, 0, 0, 0))
            transparent.paste(
                watermark,
                ((input_width - watermark_width) // 2, (input_height - watermark_height) // 2),
                watermark
            )

            # Apply watermark on the image
            watermarked_image = Image.alpha_composite(image.convert("RGBA"), transparent)
            watermarked_image = watermarked_image.convert("RGB")

            # Save the watermarked image and send it in the chat
            watermarked_image.save("watermarked_image.png")
            await ctx.send(file=discord.File("watermarked_image.png"))

        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

async def setup(bot):
    await bot.add_cog(Watermark(bot))
