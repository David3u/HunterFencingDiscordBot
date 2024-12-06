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
import typing


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

def ep(id, amt):
	id = str(id)
	load_data()
	if id not in data["ep"]:
		data["ep"][id] = 0
	data["ep"][id] += amt
	save_data() 
	return data["ep"][id] 

def get_ep(id):
	id = str(id)
	load_data() 
	if id not in data["ep"]:
		data["ep"][id] = 0
		save_data() 
	return data["ep"][id] 

def jp(id, amt):
	id = str(id)
	load_data()
	if id not in data["jp"]:
		data["jp"][id] = 0
	data["jp"][id] += amt
	save_data() 
	return data["jp"][id] 

def get_jp(id):
	id = str(id)
	load_data() 
	if id not in data["jp"]:
		data["jp"][id] = 0
		save_data() 
	return data["jp"][id] 

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

@bot.tree.command()
async def locker_codes(interaction: discord.Interaction):
	await interaction.response.send_message("https://cdn.discordapp.com/attachments/628748709081120770/876904561229582376/image0.jpg?ex=6744ca83&is=67437903&hm=f5c74c8cd36148675c265f3c8a4f62652160faf961869827e4a5967ad3043628&", ephemeral=True)

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
		await interaction.response.send_message(f"{interaction.user.mention} held lunge for {held_time} seconds. You are position `{data['leaderboard'].index([held_time, interaction.user.id]) + 1}` on the leaderboard.\nYou got `{jp(interaction.user.id, held_time//40)}` Jeff points!")

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
		self.view = FinishView(timeout = 700)


		await interaction.response.send_message(f"Started lunge timer! <t:{int(time.time())}:R>", ephemeral = True, view = self.view)
		
		self.view.message = await interaction.original_response()

		self.view.restart_timer()
		self.view.channel = self.channel
		await self.view.wait()

@bot.tree.command()
async def get_leaderboard(interaction: discord.Interaction, user: typing.Optional[discord.Member]):
	if user == None:
		load_data()
		lb = data["leaderboard"]
		st = ""
		i = 0
		for e in lb[:10]:
			i += 1
			st += f"{i} `{e[0]}` - {(await interaction.guild.fetch_member(e[1])).mention}\n"
		embed = discord.Embed(title = "Global Lunge Time Leaderboard", description = st)
		await interaction.response.send_message(embed = embed)
	else:
		load_data()
		lb = data["leaderboard"]
		st = ""
		i = 1
		s = 1
		for e in lb:
			if i > 10:
				break
			if e[1] == user.id:
				st += f"{s} `{e[0]}` - {user.mention}\n"
				i += 1

			s += 1
		embed = discord.Embed(title = "Personal Lunge Time Leaderboard", description = st)
		await interaction.response.send_message(embed = embed)
@bot.tree.command() 
async def personal_leaderboard(interaction: discord.Interaction, user: typing.Optional[discord.Member]):
	if user == None:
		user = interaction.user
	load_data()
	lb = data["leaderboard"]
	st = ""
	i = 1
	s = 1
	for e in lb:
		if i > 10:
			break
		if e[1] == user.id:
			st += f"{s} `{e[0]}` - {user.mention}\n"
			i += 1

		s += 1
	embed = discord.Embed(title = "Personal Lunge Time Leaderboard", description = st)
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

@bot.tree.command()
async def balance(interaction:discord.Interaction):
	embed = discord.Embed(title = "Your account balance", color = 0xffffff)
	embed.add_field(name = "Jeff points", value = f"`{get_jp(interaction.user.id)}`")
	embed.add_field(name = "Eugene points", value = f"`{get_ep(interaction.user.id)}`")
	await interaction.response.send_message(embed = embed)

@bot.tree.command()
async def exchange(interaction: discord.Interaction, amount: int):
	if amount < 0:
		await interaction.response.send_message("no you")
		return
	if get_jp(interaction.user.id) >= amount * 40:
		jp(interaction.user.id, -40 * amount)
		ep(interaction.user.id, amount)
		embed = discord.Embed(title = "Your account balance", color = 0xffffff)
		embed.add_field(name = "Jeff points", value = f"`{get_jp(interaction.user.id)}`")
		embed.add_field(name = "Eugene points", value = f"`{get_ep(interaction.user.id)}`")
		await interaction.response.send_message(f"You purchased `{amount}` Eugene Points for `{40 * amount}` Jeff points.", embed = embed, ephemeral =True)
	else:
		await interaction.response.send_message("Ur broke")

@bot.tree.command()
async def give_jp(interaction: discord.Interaction, target: discord.Member, amount: int):
	if interaction.user.id == 1027233463520210984:
		await interaction.response.send_message(jp(target.id, amount), ephemeral =True)
	else:
		if amount <= get_jp(interaction.user.id):
			jp(interaction.user.id, -1 * amount)
			jp(target.id, amount)
			await interaction.response.send_message(f"{interaction.user.mention} gave `{amount}` Jeff Points to {target.mention}")

@bot.tree.command()
async def coinflip(interaction: discord.Interaction, amount: int, heads: bool):
	if amount > get_jp(interaction.user.id):
		await interaction.response.send_message("ur broke", ephemeral = True)
		return 
	if random.random() < 0.4:
		jp(interaction.user.id, amount)
		if heads:
			await interaction.response.send_message(f"The coin landed on HEADS! You gained `{amount}` Jeff Points. You now have `{get_jp(interaction.user.id)}` Jeff Points.")
		else:
			await interaction.response.send_message(f"The coin landed on TAILS! You gained `{amount}` Jeff Points. You now have `{get_jp(interaction.user.id)}` Jeff Points.")
	else:
		jp(interaction.user.id, -1 * amount)
		if heads:
			await interaction.response.send_message(f"The coin landed on TAILS. You lost `{amount}` Jeff Points. You now have `{get_jp(interaction.user.id)}` Jeff Points.")
		else:
			await interaction.response.send_message(f"The coin landed on HEADS! You lost `{amount}` Jeff Points. You now have `{get_jp(interaction.user.id)}` Jeff Points.")


def rps(id1, id2, m1, m2, w):
	dct = ["Rock", "Paper", "Scissors"]
	if m1 == m2:
		jp(id1.id, w)
		jp(id2.id, w)
		return f"It was a tie!\n{id1.mention} chose {dct[m1]}. {id2.mention} chose {dct[m2]}."
	if m2 == (m1 + 1) % 3:
		jp(id2.id, w * 2)
		return f"{id2.mention} won `{w}` Jeff Points!\n{id1.mention} chose {dct[m1]}. {id2.mention} chose {dct[m2]}."
	else:
		jp(id1.id, w * 2)
		return f"{id1.mention} won `{w}` Jeff Points!\n{id1.mention} chose {dct[m1]}. {id2.mention} chose {dct[m2]}."


class RPSWait(discord.ui.View):
	user = None
	wager = 0
	move = 0
	async def disable_button(self):
		for item in self.children:
			item.disabled = True
			
	async def on_timeout(self) -> None:
		jp(self.user.id, self.wager)
		await self.disable_button()
		await self.message.edit(view = disabledM1())

	
	@discord.ui.button(
		label = "Rock",
		style = discord.ButtonStyle.success
	)
	async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):

		if get_jp(interaction.user.id) < self.wager:
			await interaction.response.send_message("Ur too broke", ephemeral = True)
			return
		if interaction.user.id == self.user.id:
			await interaction.response.send_message("U cant play with ur self", ephemeral=True)
			return 

		jp(interaction.user.id, -1 * self.wager)
		
		await interaction.response.send_message(rps(self.user, interaction.user, self.move, 0, self.wager))

		await self.message.edit(view = disabledM1())

	@discord.ui.button(
		label = "Paper",
		style = discord.ButtonStyle.success
	)
	async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):

		if get_jp(interaction.user.id) < self.wager:
			await interaction.response.send_message("Ur too broke", ephemeral = True)
			return

		if interaction.user.id == self.user.id:
			await interaction.response.send_message("U cant play with ur self", ephemeral=True)
			return 

		jp(interaction.user.id, -1 * self.wager)
		
		await interaction.response.send_message(rps(self.user, interaction.user, self.move, 1, self.wager))

		await self.message.edit(view = disabledM1())

	@discord.ui.button(
		label = "Scissors",
		style = discord.ButtonStyle.success
	)
	async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):

		if get_jp(interaction.user.id) < self.wager:
			await interaction.response.send_message("Ur too broke", ephemeral = True)
			return

		if interaction.user.id == self.user.id:
			await interaction.response.send_message("U cant play with ur self", ephemeral=True)
			return 

		jp(interaction.user.id, -1 * self.wager)
		
		await interaction.response.send_message(rps(self.user, interaction.user, self.move, 2, self.wager))

		await self.message.edit(view = disabledM1())

class disabledM1(discord.ui.View):
	@discord.ui.button(
		label = "Rock",
		style = discord.ButtonStyle.gray,
		disabled=True
	)
	async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
		pass

	@discord.ui.button(
		label = "Paper",
		style = discord.ButtonStyle.gray,
		disabled=True
	)
	async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
		pass

	@discord.ui.button(
		label = "Scissors",
		style = discord.ButtonStyle.gray,
		disabled=True
	)
	async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
		pass
		
class RPSMoveOne(discord.ui.View):
	user = None
	wager = 0
	async def disable_button(self):
		for item in self.children:
			item.disabled = True
			
	async def on_timeout(self) -> None:
		jp(self.user.id, self.wager)
		await self.disable_button()
		await self.message.edit(view = disabledM1())

	
	@discord.ui.button(
		label = "Rock",
		style = discord.ButtonStyle.success
	)
	async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):

		wait = RPSWait(timeout = 400)
		wait.wager = self.wager 
		wait.move = 0
		wait.user = self.user
		embed = discord.Embed(title=f"{self.user.display_name} wants to play Rock Paper Scissors!", description=f"Wager: `{self.wager}` Jeff Points.", color = 0x00ff00)
		await interaction.response.send_message(embed = embed, view = wait)
		await self.message.edit(view = disabledM1())
		wait.message = await interaction.original_response()

	@discord.ui.button(
		label = "Paper",
		style = discord.ButtonStyle.success
	)
	async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):

		wait = RPSWait(timeout = 400)
		wait.wager = self.wager 
		wait.move = 1
		wait.user = self.user
		embed = discord.Embed(title=f"{self.user.display_name} wants to play Rock Paper Scissors!", description=f"Wager: `{self.wager}` Jeff Points.", color = 0x00ff00)
		await interaction.response.send_message(embed = embed, view = wait)
		await self.message.edit(view = disabledM1())
		wait.message = await interaction.original_response()

	@discord.ui.button(
		label = "Scissors",
		style = discord.ButtonStyle.success
	)
	async def Scissors(self, interaction: discord.Interaction, button: discord.ui.Button):

		wait = RPSWait(timeout = 400)
		wait.wager = self.wager 
		wait.move = 2
		wait.user = self.user
		embed = discord.Embed(title=f"{self.user.display_name} wants to play Rock Paper Scissors!", description=f"Wager: `{self.wager}` Jeff Points.", color = 0x00ff00)
		await interaction.response.send_message(embed = embed, view = wait)
		await self.message.edit(view = disabledM1())
		wait.message = await interaction.original_response()


@bot.tree.command()
async def rock_paper_scissors(interaction: discord.Interaction, wager: int):
	if wager > get_jp(interaction.user.id):
		await interaction.response.send_message("Ur broke!", ephemeral = True)
		return 
	if wager < 1:
		await interaction.response.send_message("Are you emily? (bad at gambling)", ephemeral = True)
		return 

	embed = discord.Embed(title = "Choose your move", color = 0xbbbbbb)
	jp(interaction.user.id, -1 * wager)
	m1 = RPSMoveOne()
	m1.wager = wager 
	m1.user = interaction.user
	await interaction.response.send_message(embed = embed, view = m1, ephemeral=True)
	m1.message = await interaction.original_response()


bot.run(str(os.getenv("TOKEN")))


