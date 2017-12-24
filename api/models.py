from bson.objectid import ObjectId
from collections import defaultdict
from copy import deepcopy
from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
    MapField,
    ObjectIdField,
    StringField
)

from api.exceptions import NotFoundException


class Seat(EmbeddedDocument):
    seat_id = StringField(required=True)
    is_free = BooleanField(default=True)
    is_blocked = BooleanField(default=False)

    def reserve(self) -> bool:
        """
        Reserves a seat if it is available
        """
        if self.is_free and not self.is_blocked:
            self.is_free = False
            return True

        return False

    def block(self) -> bool:
        """
        Blocks a seat due a technical purpose
        """
        if not self.is_blocked and self.is_free:
            self.is_blocked = True
            self.is_free = False
            return True

        return False

    def to_dict(self) -> dict:
        """
        A Seat's dict representation
        """
        return {
            'seat_id': self.seat_id,
            'is_free': self.is_free,
            'is_blocked': self.is_blocked
        }


class Row(EmbeddedDocument):
    row_id = StringField(required=True)
    rank = StringField(required=True)
    seats = ListField(EmbeddedDocumentField(Seat))

    @property
    def free_seats(self) -> bool:
        """
        The number of free seats in the row
        """
        return sum([1 for seat in self.seats if seat.is_free])

    @property
    def is_full(self) -> bool:
        """
        Check if the row is full
        """
        return self.free_seats == 0

    @property
    def number_seats(self) -> int:
        """
        The number of seats in the row
        """
        return len(self.seats)

    def add_seat(self, seat: Seat):
        """
        Add a seat to the row
        """
        self.seats.append(seat)

    @classmethod
    def create_row(cls, row_json: dict, row_number: str) -> 'Row':
        """
        Parse row related part of the JSON in the form of
            {
              "row_rank": 2,
              "num_seats": 10,
              "num_rows": 2,
              "order": "sequential"
            }

        A row is a group of seats which can be sequentially ordered (passing "sequential" in order) or
            ordered by outside in (passing "non-sequential in order)
        """
        row = cls(row_id=row_number, rank=row_json['row_rank'])
        is_even = row_json['num_seats'] % 2 == 0
        current_id = 0

        for _ in range(1, row_json['num_seats'] + 1):
            if row_json['order'] == 'sequential':
                current_id += 1

            elif row_json['order'] == 'non-sequential':
                # Arrange seats like 1 3 5 4 2 in the case the number of seats is odd (5)
                # or 1 3 5 6 4 2 in the case the number of seats is even (6)
                if current_id == 0:
                    current_id += 1
                elif is_even and current_id + 1 == row_json['num_seats']:
                    current_id += 1
                elif not is_even and current_id == row_json['num_seats']:
                    current_id -= 1
                elif current_id % 2 == 1:
                    current_id += 2
                else:
                    current_id -= 2

            row.add_seat(Seat(seat_id=str(current_id)))

        return row

    def number_contiguous_seats(self) -> dict:
        """
        Gives the number of contagious empty seats and bucket them by number of contagious empty seats
        {
            "1": [1, 6],
            "2": [3, 4]
        }

        There is 2 empty isolated seats (1 and 6) and there is one 2-contagious empty seats (3, 4)
        """
        available_seats = defaultdict(list)

        if self.is_full:
            return available_seats

        current_sequence = []

        for index, seat in enumerate(self.seats):
            if seat.is_free and not seat.is_blocked:
                current_sequence.append(seat)
                continue

            available_seats[len(current_sequence)].extend(current_sequence)
            current_sequence = []

        if len(current_sequence):
            available_seats[len(current_sequence)].extend(current_sequence)

        return available_seats

    def block(self, seat_id: int) -> bool:
        """
        Marks a seat as blocked
        """
        for seat in self.seats:
            if seat.seat_id == str(seat_id):
                return seat.block()

        return False

    def to_dict(self) -> dict:
        """
        A Row's dict representation
        """
        return {
            'row_id': self.row_id,
            'rank': self.rank,
            'seats': [seat.to_dict() for seat in self.seats]
        }


class Section(EmbeddedDocument):
    type = StringField(required=True)
    rows = MapField(ListField(EmbeddedDocumentField(Row)))

    def add_row(self, row: Row) -> None:
        """
        Add a row to the section
        """
        if row.rank not in self.rows:
            self.rows[row.rank] = []

        self.rows[row.rank].append(row)

    def get_rows_with_seats(self) -> list:
        """
        Get all the rows with free seats
        """
        return [row for row in self.rows if row.free_seats > 0]

    def make_reservation(self, group: list) -> list:
        """
        Makes the reservation for groups of people

        The number of people to be seated is the elements in the array and the array index represents
            the row rank. [2, 4] means 2 people to be seated in 1st rank, 4 people to be seated in 2nd rank

        The availability structure is built as follow
            {
                "1st Rank": {
                    "1" : {
                        "1": [Seat 3],
                        "2": [Seat 1, Seat 2, Seat 4, Seat 5]
                    }
                }
            }

        meaning
            Row 1 in 1st Rank has 1 isolated seats (Seat 3)
            Row 1 in 1st Rank has 2 2-contiguous seats (Seat 1, Seat 2 and Seat 4, Seat 5)

        A huge improvement would be keeping this structure cached so we do not need to
        generate it for every group of reservations
        """

        if len(group) > len(self.rows.keys()):
            return group

        availability = {}

        for rank, rows in self.rows.items():
            availability[rank] = defaultdict(dict)

            for row in rows:
                availability[rank][row.row_id] = row.number_contiguous_seats()

        to_seat = group[:]

        for rank_index, num_people in enumerate(group):
            for i, rank in enumerate(self.rows):
                if i == rank_index:
                    rank_availability = availability[rank]

            for available_seats in rank_availability.values():
                if len(available_seats.get(num_people, [])):  # We found exactly num_people contiguous seats
                    for i in range(num_people):
                        available_seats[num_people][i].reserve()
                        to_seat[rank_index] -= 1
                    break
                else:  # let's try rows with more available contiguous seats OR let's split the group
                    for num_available in available_seats.keys():
                        if num_available <= num_people:
                            continue

                        for i in range(num_people):
                            available_seats[num_available][i].reserve()
                            to_seat[rank_index] -= 1

                        if to_seat[rank_index] == 0:
                            break

                    if to_seat[rank_index] > 0:
                        for num_available in reversed(list(available_seats.keys())):
                            if num_available >= num_people:
                                continue

                            for i in range(min(num_available, to_seat[rank_index])):
                                available_seats[num_available][i].reserve()
                                to_seat[rank_index] -= 1

                            if to_seat[rank_index] == 0:
                                break

                    if to_seat[rank_index] == 0:
                        break

                if to_seat[rank_index] == 0:
                    break

        return to_seat

    def block(self, row_id: int, *args, **kwargs) -> bool:
        """
        Interface to mark a seat in a row as blocked
        """
        for _, rows in self.rows.items():
            for row in rows:
                if row.row_id == str(row_id):
                    return row.block(*args, **kwargs)

        return False

    @classmethod
    def create_section(cls, section_json: dict) -> 'Section':
        """
        Parse the section part of the JSON in form of
        "sections": [
            {
              "section_type": "house",
              "rows": [...]
            }
        ]

        A section is a group of rows
        """
        section = cls(type=section_json['section_type'])

        for row_type in section_json['rows']:
            for _ in range(row_type['num_rows']):
                section.add_row(Row.create_row(row_type, next(id_generator)))

        return section

    def to_dict(self) -> dict:
        """
        A Section's dict representation
        """
        return {
            'type': self.type,
            'rows': {
                rank: [row.to_dict() for row in rows]
                for rank, rows in self.rows.items()
            }
        }


class Event(EmbeddedDocument):
    id = ObjectIdField(required=True, default=lambda: ObjectId())
    event_name = StringField()
    created_at = DateTimeField()
    date = DateTimeField()
    sections = MapField(EmbeddedDocumentField(Section))

    def make_reservation(self, section_type: int, *args, **kwargs) -> bool:
        """
        Interface to make a reservation for a group of people for a given section

        A list zero'ed will be returned if all people found a seat
            otherwise the number of people without a seat will be returned in the list
        """
        return self.sections[section_type].make_reservation(*args, **kwargs)

    def block(self, section_type, *args, **kwargs):
        return self.sections[section_type].block(*args, **kwargs)

    def to_dict(self) -> dict:
        """
        An Event's dict representation
        """
        return {
            'id': str(self.id),
            'event_name': self.event_name,
            'created_at': self.created_at.isoformat(),
            'date': self.date.isoformat(),
            'sections': {
                section_type: section.to_dict()
                for section_type, section in self.sections.items()
            }
        }


class Venue(Document):
    venue_name = StringField()
    input_json = DictField()
    base_layout = MapField(EmbeddedDocumentField(Section))
    events = ListField(EmbeddedDocumentField(Event))

    meta = {'collection': 'venue'}

    def create_venue(self, sections: dict) -> None:
        """
        Builds the venue seating plan from the JSON defining the seating sections

        A section has the format of
        "sections": [
            {
                "section_type": "house",
                "rows": [
                    {
                        "row_rank": "1st Rank",
                        "num_seats": 8,
                        "num_rows": 3,
                        "order": "non-sequential"
                    }
                    ...
                ]
            }
        """
        reset_generator()

        for section in sections:
            self.base_layout[section['section_type']] = Section.create_section(section)

        self.save(load_bulk=False)

    def create_event(self, date: datetime, event_name: str ='Test Event') -> Event:
        """
        Creates an event in the venue
        """
        self.events.append(Event(
            event_name=event_name,
            created_at=datetime.now(),
            date=date,
            sections=deepcopy(self.base_layout)
        ))

        self.save()

        return self.events[-1]

    def get_event(self, event_id: str) -> Event:
        """
        Get an event occurring in the venue
        """
        for event in self.events:
            if str(event.id) == event_id:
                return event

        raise NotFoundException

    def make_reservation(self, event_id: str, *args, **kwargs) -> list:
        """
        Interface to make a reservation for a group of people for a given event and section

        A list zero'ed will be returned if all people found a seat
            otherwise the number of people without a seat will be returned in the list
        """
        event = self.get_event(event_id)
        result = event.make_reservation(*args, **kwargs)
        self.save()

        return result

    def block(self, event_id: str, *args, **kwargs) -> bool:
        """
        Interface to mark a seat as blocked
        """
        event = self.get_event(event_id)
        result = event.block(*args, **kwargs)

        if result:
            self.save()

        return result

    def to_dict(self) -> dict:
        """
        A Venue's dict representation
        """
        return {
            'id': str(self.id),
            'venue_name': self.venue_name,
            'input_json': self.input_json,
            'base_layout': {
                section_type: section.to_dict()
                for section_type, section in self.base_layout.items()
            },
            'events': [event.to_dict() for event in self.events]
        }


def row_number_generator():
    """
    Generator to get numbers from 1 to 9999
    """
    for num_row in range(1, 9999):
        yield str(num_row)


def reset_generator():
    """
    Reset the module level generator
    """
    global id_generator
    id_generator = row_number_generator()


id_generator = row_number_generator()
