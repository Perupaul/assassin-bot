import discord
import random
from assassin import read_assassins, Assassin, save_assassins_to_json


async def target_kill_response(channel, assassin, assassins):
    assassin.eliminate_target(assassins)
    if assassin.target == assassin:
        response = '**CONGRATULATIONS!!!**\nYou are the last one standing!\nMay everyone fear you forever,\nAmen'
        await channel.send(response)
    else:
        response = random.choice([
            'Excellently done.\n',
            'They never saw it coming.\n',
            'Another one bites the dust.\n'
        ])
        response += assign_next_target(assassin, True)
        await channel.send(response)
        await send_image(f'photos/{assassin.target.image}', channel)


async def attacker_kill_response(channel, assassin, assassins, client):
    assassin.eliminate_attacker(assassins)
    await channel.send('Well done, that\'s an elimination in your favor.')
    # send updated target to new attacker
    attacker_channel = client.get_channel(assassin.attacker.channel_id)
    response = 'Your target was killed in self defense\n'
    response += assign_next_target(assassin.attacker, True)
    await attacker_channel.send(response)
    await send_image(f'photos/{assassin.image}', attacker_channel)


async def kill_response(message, assassin, assassins):
    target = None
    for spy in assassins:
        if spy.passcode == str(message.content).lower():
            target = spy
            break
    target.attacker.target = target.target
    assassin.kill_count += 1
    target.die(assassins)
    await message.channel.send('A successful elimination, you\'re on your way to victory!')


async def help_response(message, assassin):
    if assassin.target != assassin:
        await message.channel.send(
            f'Your personal passcode is **{assassin.passcode}**'
        )
        await message.channel.send(
            f'Your target is:\nName: **{assassin.target.name}**\nMajor: **{assassin.target.major}**'
        )


async def free_for_all(assassins, client):
    general_channel = client.get_channel(1036817423476736083)
    await general_channel.send('It is free for all time, these are the remaining spies')
    for assassin in assassins.values():
        if not assassin.dead:
            await general_channel.send(f'Name: **{assassin.name}\nMajor: **{assassin.major}')
            await send_image(f'photos/{assassin.image}', general_channel)


async def send_image(image, channel):
    try:
        with open(image, 'rb') as file:
            # Says unexpected type, but it works fine.
            # noinspection PyTypeChecker
            image = discord.File(file)
            await channel.send(file=image)
    except FileNotFoundError:
        return


async def setup(assassins, client):
    # assassins is a dict
    for assassin in assassins.values():
        channel = client.get_channel(int(assassin.channel_id))
        text = '**Welcome to Espionage**\n'
        text += f'Your passcode is: {assassin.passcode}\n'
        text += assign_next_target(assassin)
        await channel.send(text)
        await send_image(f'photos/{assassin.target.image}', channel)


async def master_kill(message, assassins, client, self_defense):
    user_message = str(message.content).lower()
    split_message = user_message.split(' ')
    if not (len(split_message) == 3 or len(split_message) == 2):
        await message.channel.send('The command was poorly formatted, it should be "kill [passcode] '
                                   '[defense (as the word defense or blank)]')
    victim_code = split_message[1]
    victim = get_assassin_from_code(victim_code, assassins)
    if victim is None:
        return
    if self_defense:
        attacker = victim.target
        attacker_channel = client.get_channel(attacker.channel_id)
        await attacker_channel.send(f'You eliminated {victim.name}')
        await attacker_kill_response(attacker_channel, attacker, assassins, client)
    else:
        attacker = victim.attacker
        attacker_channel = client.get_channel(attacker.channel_id)
        await target_kill_response(attacker_channel, attacker, assassins)
    await message.channel.send(f'Eliminated {victim.name}')


async def undo_kill(message, assassins, client):
    user_message = str(message.content).lower()

    if len(user_message.split(' ')) != 2:
        await message.channel.send('The command was poorly formatted, it should be "undo [passcode]"')

    # Find the victim
    victim_code = user_message.split(' ')[1]
    victim = get_assassin_from_code(victim_code, assassins)
    if victim is None:
        return
    assert isinstance(victim, Assassin)

    # Find other characters
    attacker = victim.attacker
    target = victim.target
    assert attacker.target == target, 'the victim hasn\'t been killed'
    assert victim.dead, 'the victim isn\'t dead'

    # Reset to previous targets
    attacker.target = victim
    attacker.kill_count -= 1
    target.attacker = victim
    victim.generate_new_passcode(assassins)
    victim.dead = False
    save_assassins_to_json(assassins)

    # tell victim they're alive again
    victim_channel = client.get_channel(victim.channel_id)
    await victim_channel.send(f'Your death has been undone. You\'re basically a zombie now! Wow that\'s really cool.\n'
                              f'Your target is the same as before\n Your new passcode is **{victim.passcode}**')

    # send info to attacker
    attacker_channel = client.get_channel(attacker.channel_id)
    await attacker_channel.send(f'Your elimination of {victim.name} has been undone\n{assign_next_target(attacker)}')
    await send_image(f'photos/{victim.image}', attacker_channel)

    # Tell user it worked
    await message.channel.send(f'The death of {victim.name} has been undone.')


def assign_next_target(assassin, new=False) -> str:
    return f'Your {"new " if new else ""}target is:\nName: **{assassin.target.name}**\nMajor: ' \
           f'**{assassin.target.major}**'


def get_assassin_from_code(code: str, assassins: dict):
    victim_code = code
    for discord_tag in assassins:
        if assassins[discord_tag].passcode == victim_code:
            return assassins[discord_tag]
    return None


def run_discord_bot():
    token = 'MTAzNjgxODA2OTU5MjQ4MTgyMg.G2YUcr.lHtotkM1BTH0fRoL4aW_7gX9OoaEN7ghwH7OOg'
    intents = discord.Intents.default()
    # noinspection PyUnresolvedReferences
    intents.message_content = True
    client = discord.Client(intents=intents)

    # Game info
    assassins = read_assassins()

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')

    @client.event
    async def on_message(message):
        username = str(message.author)
        user_message = str(message.content).lower()
        channel = str(message.channel)

        # We don't want an infinite loop
        if username == str(client.user):
            return

        # Make sure it's somewhere we care about
        if channel == 'general':
            return
        if channel == 'master':
            if user_message == 'setup':
                await setup(assassins, client)
            if 'kill' in user_message:
                await master_kill(message, assassins, client, 'defense' in user_message)
            if 'undo' in user_message:
                await undo_kill(message, assassins, client)
            if user_message == 'ping':
                await message.channel.send('pong')
            if 'free for all' in user_message:
                await free_for_all(assassins, client)
            return

        # Find current assassin
        try:
            assassin = assassins[username]
            if assassin.dead:
                return
        except KeyError:
            await message.channel.send(
                f'{username} isn\'t listed as one of the assassins. Contact @Perupaul so we can get you back to murder.'
            )
            return

        assassin_passcodes = [x.passcode for x in assassins.values()]

        # Successful kill
        if user_message == assassin.target.passcode:
            await target_kill_response(message.channel, assassin, assassins)
        elif user_message == assassin.attacker.passcode:
            await attacker_kill_response(message.channel, assassin, assassins, client)
        elif user_message == 'help':
            await help_response(message, assassin)
        elif user_message in assassin_passcodes:
            await kill_response(message, assassin, assassins.values())

    client.run(token)

if __name__ == '__main__':
    run_discord_bot()