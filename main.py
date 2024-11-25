import os
from dotenv import load_dotenv
load_dotenv() 

import discord
from discord.ext.commands import Bot
from discord.ext import commands
from discord import app_commands
import asyncio
import json
import random
import string
import time


######
# CONFIG

guild_id = 628732169069789205


######


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents = intents)


data = {}

def load_data():
	global data
	f = open("mydata.json")
	data = json.load(f)
	f.close()

def save_data():
	global data
	with open("mydata.json","w") as f:
		json.dump(data, f)
		



@bot.event 
async def on_ready():
	bot.tree.copy_global_to(guild=discord.Object(id=guild_id))
	await bot.tree.sync(guild=discord.Object(id=guild_id))
	
	await asyncio.sleep(2)
	activity = discord.Activity(
		name=f"HCHS Fencing", type=discord.ActivityType.watching
	)

	await bot.change_presence(activity=activity)

	load_data()
	global data

@bot.tree.command()
async def drive_link(interaction: discord.Interaction):
	await interaction.response.send_message("https://drive.google.com/drive/folders/1tU7M-_EPOVlBaus13XrG2qZkaFWsT7xp", ephemeral = True)

class DisabledFinishView(discord.ui.View):
	@discord.ui.button(
		label = "Finish Lunge",
		style = discord.ButtonStyle.gray,
		disabled=True
	)
	async def verify_link(self, interaction: discord.Interaction, button: discord.ui.Button):
		pass


class FinishView(discord.ui.View):
	message = None
	channel = None
	start_time = time.time()

	def restart_timer(self):
		self.start_time = time.time()

	async def disable_button(self):
		for item in self.children:
			item.disabled = True
			
	async def on_timeout(self) -> None:
		await self.disable_button()
	
	@discord.ui.button(
		label = "Finish Lunge",
		style = discord.ButtonStyle.danger
	)
	async def verify_link(self, interaction: discord.Interaction, button: discord.ui.Button):
		load_data()
		held_time = round(time.time() - self.start_time, 1)
		data["leaderboard"].append([held_time, interaction.user.id])
		data["leaderboard"].sort(reverse = True) 
		save_data()
		await self.message.edit(view = DisabledFinishView(), content = f"Started lunge timer! `{held_time} seconds ago`")
		await interaction.response.send_message(f"{interaction.user.mention} held lunge for {held_time} seconds. You are position `{data['leaderboard'].index([held_time, interaction.user.id]) + 1}` on the leaderboard.")

class DisabledView(discord.ui.View):
	@discord.ui.button(
		label = "Start Lunge",
		style = discord.ButtonStyle.gray,
		disabled=True
	)
	async def verify_link(self, interaction: discord.Interaction, button: discord.ui.Button):
		pass

class StartView(discord.ui.View):
	channel = None
	user = None
	async def disable_button(self):
		for item in self.children:
			item.disabled = True
			
	async def on_timeout(self) -> None:
		await self.channel.send("The lunge time is over")
		await self.disable_button()
		embed = discord.Embed(title = "It was time to hold lunge position!", description = "Called by " + self.user.mention, color=0xbbbbbb)
		await self.message.edit(embed= embed, view = DisabledView())
	
	@discord.ui.button(
		label = "Start Lunge",
		style = discord.ButtonStyle.success
	)
	async def verify_link(self, interaction: discord.Interaction, button: discord.ui.Button):
		self.view = FinishView(timeout = 400)


		await interaction.response.send_message(f"Started lunge timer! <t:{int(time.time())}:R>", ephemeral = True, view = self.view)
		
		self.view.message = await interaction.original_response()

		self.view.restart_timer()
		self.view.channel = self.channel
		await self.view.wait()

@bot.tree.command()
async def get_leaderboard(interaction: discord.Interaction):
	load_data()
	lb = data["leaderboard"]
	st = ""
	i = 1
	for e in lb[:10]:
		st += f"{i}. `{e[0]}` - {(await interaction.guild.fetch_member(e[1])).mention}\n"
	embed = discord.Embed(title = "Lunge Time Leaderboard", description = st)
	await interaction.response.send_message(embed = embed)

@bot.tree.command()
async def ping_lunge(interaction: discord.Interaction):
	global data
	load_data()
	admin_role = discord.utils.get(interaction.guild.roles, id=data["config"]["admin_role"])

	if time.time() - data["last_ping"] < 2000 and not admin_role in interaction.user.roles:
		await interaction.response.send_message("Please wait " + str(2000 - (time.time() - data["last_ping"])) + " seconds before trying to mass ping people again thanks!", ephemeral = True)
		return
	data["last_ping"] = time.time()

	save_data()

	await interaction.response.send_message("ok", ephemeral = True)

	role = discord.utils.get(interaction.guild.roles, id=data["config"]["ping_role"])
	embed = discord.Embed(title = "It's time to hold lunge position!", description = "Called by " + interaction.user.mention, color=0x00ff00)

	finish_view = StartView(timeout = 120)

	finish_view.message = await interaction.channel.send( role.mention, embed = embed, view = finish_view)

	finish_view.channel = interaction.channel
	finish_view.user = interaction.user
	await finish_view.wait()
      

bot.run(str(os.getenv("TOKEN")))


