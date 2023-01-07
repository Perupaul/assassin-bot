import csv
from assassin import Assassin, save_assassins_to_json
import random



def select_targets(assassins: list):
    assert len(assassins) > 1, 'people should be longer than 1 person'
    index_list = []  # we don't want to pop from the actual people list because it affects the global variable
    for i in range(len(assassins)):
        index_list.append(i)
    first_person = assassins[index_list.pop(random.randrange(0, len(index_list)))]
    previous_person = first_person
    while len(index_list) > 0:
        next_person = assassins[index_list.pop(random.randrange(0, len(index_list)))]
        previous_person.target = next_person
        previous_person.target_id = next_person.id
        next_person.attacker = previous_person
        next_person.attacker_id = previous_person.id
        previous_person = next_person
    previous_person.target = first_person
    previous_person.target_id = first_person.id
    first_person.attacker = previous_person
    first_person.attacker_id = previous_person.id


def main():
    with open('Espionage Challenge.csv', 'r', newline='') as people_data:
        assassins = []
        reader = csv.reader(people_data)
        used_passcodes = set()
        for i, row in enumerate(reader):
            # Don't want the title row
            if i == 0:
                continue
            # i basically starts with 1, which is the first (zeroth) element
            assassins.append(Assassin.assassin_from_csv(row, i - 1, used_passcodes))
        select_targets(assassins)
        save_assassins_to_json(assassins)


if __name__ == '__main__':
    main()