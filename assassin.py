import random
import json
import string


class Assassin:
    def __init__(
            self, assassin_id, name, major, image, discord, dead=False,
            target_id=None, attacker_id=None, passcode=None, kill_count=0, channel_id=0
    ):
        self.id = assassin_id
        self.name = name
        self.major = major
        self.image = image
        self.dead = dead
        self.target_id = target_id
        self.target = None  # for now
        self.attacker_id = attacker_id
        self.attacker = None  # for now
        self.discord = discord
        self.passcode = passcode
        self.kill_count = kill_count
        self.channel_id = channel_id

    @staticmethod
    def assassin_from_csv(csv_data, n, used_passcodes: set):
        assassin_id = n
        name = csv_data[1]
        major = csv_data[2]
        image = csv_data[3]
        discord = csv_data[4]
        passcode = ''.join(random.choices(string.ascii_lowercase, k=5))
        while passcode in used_passcodes:
            passcode = ''.join(random.choices(string.ascii_lowercase, k=5))
        used_passcodes.add(passcode)
        channel_id = int(csv_data[7])
        return Assassin(
            assassin_id, name, major, image, discord, passcode=passcode, channel_id=channel_id
        )

    @staticmethod
    def assassin_from_json(json_data: dict):
        assassin_id = json_data['id']
        name = json_data['name']
        major = json_data['major']
        image = json_data['image']
        dead = json_data['dead']
        target_id = json_data['target_id']  # For reading from json purposes
        attacker_id = json_data['attacker_id']
        discord = json_data['discord']
        passcode = json_data['passcode']
        kill_count = json_data['kill_count']
        channel_id = int(json_data['channel_id'])
        return Assassin(
            assassin_id, name, major, image, discord, dead, target_id, attacker_id, passcode, kill_count, channel_id
        )

    def die(self, assassins):
        self.attacker.target = self.target
        self.target.attacker = self.attacker
        self.dead = True
        save_assassins_to_json(assassins)

    def eliminate_target(self, assassins):
        self.kill_count += 1
        self.target.die(assassins)

    def eliminate_attacker(self, assassins):
        self.attacker.die(assassins)
        self.kill_count += 1

    def __str__(self):
        if self.target:
            target = self.target.name
        else:
            target = None
        if self.attacker:
            attacker = self.attacker.name
        else:
            attacker = None
        return f'Assassin(id={self.id}, name={self.name}, major={self.major}, dead={self.dead}, ' \
               f'target={target}, attacker={attacker}, passcode={self.passcode}, ' \
               f'discord={self.discord})'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.id == other.id and self.name == other.name and self.major == other.major and \
               self.target_id == other.target_id and self.attacker_id == other.attacker_id and \
               self.discord == other.discord and self.passcode == other.passcode and self.dead == other.dead

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'major': self.major,
            'image': self.image,
            'dead': self.dead,
            'target_id': self.target.id if self.target else None,
            'attacker_id': self.attacker.id if self.attacker else None,
            'passcode': self.passcode,
            'discord': self.discord,
            'kill_count': self.kill_count,
            'channel_id': self.channel_id,
        }

    def generate_new_passcode(self, assassins: dict):
        used_passcodes = set()
        for assassin in assassins.values():
            used_passcodes.add(assassin.passcode)
        passcode = ''.join(random.choices(string.ascii_lowercase, k=5))
        while passcode in used_passcodes:
            passcode = ''.join(random.choices(string.ascii_lowercase, k=5))
        self.passcode = passcode


def convert_assassins_to_list(assassins):
    result = []
    for assassin in assassins.values():
        result.append(assassin)
        result.sort(key=lambda x: x.id)
    return result


def set_targets_from_ids(assassins):
    if isinstance(assassins, dict):
        assassins = convert_assassins_to_list(assassins)
    for assassin in assassins:
        target_id = assassin.target_id
        attacker_id = assassin.attacker_id
        if target_id is None:  # For testing, we haven't set
            break
        assassin.target = assassins[target_id]
        assassin.attacker = assassins[attacker_id]


def save_assassins_to_json(assassins, output_file='assassins.json'):
    if isinstance(assassins, dict):
        assassins = convert_assassins_to_list(assassins)
    data = dict()
    data['assassins'] = [assassin.to_json() for assassin in assassins]
    json_data = json.dumps(data, indent=4, sort_keys=True)
    with open(output_file, 'w') as f:
        f.write(json_data)


def read_assassins(input_file='assassins.json'):
    """
    returns a dictionary mapping to all the assassins from their discord tags
    """
    # Just reads the assassins data from assassins.json and turns them into assassin objects
    with open(input_file, 'r') as f:
        # Create Person Objects
        data = json.load(f)
        people_json = data['assassins']
        if not len(people_json) > 0:
            raise ValueError('There are no people in assassins.json')
        assassins = []
        for person in people_json:
            assassins.append(Assassin.assassin_from_json(person))

    # Set targets
    set_targets_from_ids(assassins)

    # turn into dict
    result = dict()
    for assassin in assassins:
        result[assassin.discord] = assassin
    if not len(result) == len(assassins):
        raise ValueError("multiple equal discords")
    return result


if __name__ == '__main__':
    print(read_assassins())