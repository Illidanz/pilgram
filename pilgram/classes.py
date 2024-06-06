import random
from datetime import datetime
from typing import Tuple, Dict, Any, Callable, Union

from pilgram.globals import ContentMeta


class Zone:
    """ contains info about a zone. Zone 0 should be the town to reuse the zone event system """

    def __init__(self, zone_id: int, zone_name: str, level: int, zone_description: str):
        """
        :param zone_id: zone id
        :param zone_name: zone name
        :param level: zone level, control the minimum level a player is required to be to accept quests in the zone
        :param zone_description: zone description
        """
        self.zone_id = zone_id
        self.zone_name = zone_name
        self.level = level
        self.zone_description = zone_description


class Quest:
    """ contains info about a human written or AI generated quest """

    def __init__(
            self,
            quest_id: int,
            zone: Zone,
            number: int,
            name: str,
            description: str,
            success_text: str,
            failure_text: str,
    ):
        """
        :param quest_id (int): unique id of the quest
        :param zone (Zone): zone of the quest
        :param number (int): ordered number of the quest, players do quests incrementally in the same order in each zone
        :param description (str): description of the quest
        :param success_text (str): text to send player when the quest is successful
        :param failure_text (str): text to send player when the quest is not successful
        """
        self.quest_id = quest_id
        self.zone = zone
        self.number = number
        self.name = name
        self.description = description
        self.success_text = success_text
        self.failure_text = failure_text

    def finish_quest(self, player: "Player") -> bool:
        """ return true if the player has successfully finished the quest """
        roll = random.randint(0, 11)
        if roll == 0:
            return False  # you can still get a critical failure
        result = player.level + player.gear_level + roll
        return result >= self.zone.level + (self.number * 2)

    def get_rewards(self, player: "Player") -> Tuple[int, int]:
        """ return the amount of xp & money the completion of the quest rewards """
        multiplier = self.zone.level + self.number + player.guild.level if player.guild.level else 0
        return 100 * multiplier, 180 * multiplier  # XP, Money

    def __str__(self):
        return f"*{self.name}*\n\n{self.description}"


class Progress:
    """ stores the player quest progress for each zone """

    def __init__(self, zone_progress: Dict[int, int]):
        """
        :param zone_progress:
            dictionary that contains the player quest progress in the zone, stored like this: [zone, progress]
        """
        self.zone_progress = zone_progress

    def get_zone_progress(self, zone: Zone) -> int:
        return self.zone_progress.get(zone.zone_id, 0)

    def __str__(self):
        return "\n".join(f"zone {zone}: progress {progress}" for zone, progress in self.zone_progress)

    def __repr__(self):
        return str(self.zone_progress)

    @classmethod
    def get_from_encoded_data(cls, progress_data: Any, parsing_function: Callable[[Any], Dict[int, int]]) -> "Progress":
        """
        :param progress_data:
            The data that contains the player quest progress.
            How it is stored on the database is independent of the implementation here.
        :param parsing_function:
            The function used to parse progress_data, must return the correct data format
        """
        zone_progress: Dict[int, int] = parsing_function(progress_data)
        return cls(zone_progress)


class Player:
    """ contains all information about a player """

    def __init__(
            self,
            player_id: int,
            name: str,
            description: str,
            guild: "Guild",
            level: int,
            xp: int,
            money: int,
            progress: Progress,
            gear_level: int,
            home_level: int
    ):
        """
        :param player_id (int): unique id of the player
        :param name (str): name of the player
        :param description (str): user written description of the player
        :param guild: the guild this player belongs to
        :param level (int): current player level, potentially unlimited
        :param xp (int): current xp of the player
        :param money (int): current money of the player
        :param progress (Progress): contains progress object, which tracks the player progress in each zone,
        :param gear_level (int): current gear level of the player, potentially unlimited
        :param home_level(int): current level of the home owned by the player, potentially unlimited
        """
        self.player_id = player_id
        self.name = name
        self.description = description
        self.guild = guild
        self.progress = progress
        self.money = money
        self.level = level
        self.xp = xp
        self.gear_level = gear_level
        self.home_level = home_level

    def get_required_xp(self) -> int:
        return 100 * self.level + (5 * self.level * self.level)

    def get_gear_upgrade_required_money(self) -> int:
        return 100 * self.gear_level + (self.gear_level * self.gear_level)

    def get_home_upgrade_required_money(self) -> int:
        return 1000 * self.home_level + (4 * self.home_level * self.home_level)

    def can_upgrade_gear(self) -> bool:
        return self.money >= self.get_gear_upgrade_required_money()

    def can_upgrade_home(self) -> bool:
        return self.money >= self.get_home_upgrade_required_money()

    def upgrade_gear(self):
        self.gear_level += 1
        self.money -= self.get_gear_upgrade_required_money()

    def upgrade_home(self):
        self.home_level += 1
        self.money -= self.get_home_upgrade_required_money()

    def level_up(self):
        req_xp = self.get_required_xp()
        while self.xp >= req_xp:
            self.level += 1
            self.xp -= req_xp
            req_xp = self.get_required_xp()

    def add_xp(self, amount: int) -> bool:
        """ adds xp to the player and returns true if the player leveled up """
        self.xp += amount
        if self.xp >= self.get_required_xp():
            self.level_up()
            return True
        return False

    def __str__(self):
        guild = f" | {self.guild.name} (lv. {self.guild.level})" if self.guild else ""
        return f"{self.name} | lv. {self.level}{guild}\nHome level {self.home_level}, Gear level {self.gear_level}\n\n{self.description}"

    def __repr__(self):
        return str(self.__dict__)

    @classmethod
    def create_default(cls, player_id: int, name: str, description: str) -> "Player":
        player_defaults = ContentMeta.get("defaults.player")
        return Player(
            player_id,
            name,
            description,
            player_defaults["guild"],
            player_defaults["level"],
            player_defaults["xp"],
            player_defaults["money"],
            player_defaults["progress"],
            player_defaults["gear"],
            player_defaults["home"]
        )


class Guild:
    """ Player created guilds that other players can join. Players get bonus xp & money from quests when in guilds """
    MAX_LEVEL = ContentMeta.get("guilds.max_level")
    PLAYERS_PER_LEVEL = ContentMeta.get("guilds.players_per_level")

    def __init__(self, guild_id: int, name: str, level: int, description: str, founder: Player, creation_date: datetime):
        """
        :param guild_id: unique id of the guild
        :param name: player given name of the guild
        :param level: the current level of the guild, controls how many players can be in a guild (4 * level). Max is 10
        :param description: player given description of the guild
        :param founder: the player who found the guild,
        :param creation_date: the date the guild was created
        """
        self.guild_id = guild_id
        self.name = name
        self.level = level
        self.description = description
        self.founder = founder
        self.creation_date = creation_date

    def can_add_member(self, current_members: int) -> bool:
        return current_members < self.level * self.PLAYERS_PER_LEVEL

    def can_upgrade(self) -> bool:
        return (self.level < self.MAX_LEVEL) and (self.founder.money >= self.get_upgrade_required_money())

    def get_upgrade_required_money(self) -> int:
        return 10000 * self.level + (5 * self.level * self.level)

    def upgrade(self):
        self.founder.money -= self.get_upgrade_required_money()
        self.level += 1

    def __str__(self):
        return f"*{self.name}*\nfounder: _{self.founder.name}\nsince {self.creation_date.strftime("%d %b %Y")}_\n\n{self.description}"


class ZoneEvent:
    """
        Events that happen during the day every X hours of which the player is notified.
        Players get bonus xp & money from events depending on their home level.
    """

    def __init__(self, event_id: int, zone: Zone, event_text: str):
        """
        :param event_id: unique id of the event
        :param zone: the zone that this event happens in
        :param event_text: a short text describing the event
        """
        self.event_id = event_id
        self.zone = zone
        self.event_text = event_text
        self.base_xp_value = (zone.level + 1)
        self.base_money_value = self.base_xp_value

    def __str__(self):
        return f"{self.event_text}"

    def get_rewards(self, player: Player) -> Tuple[int, int]:
        """ returns xp & money rewards for the event. Influenced by player home level """
        xp = (self.base_xp_value + player.home_level) * random.randint(1, 10)
        money = (self.base_money_value + player.home_level) * random.randint(1, 10)
        return xp, money


class AdventureContainer:
    """ Utility class to help manage player updates """

    def __init__(self, player: Player, quest: Union[Quest, None], finish_time: Union[datetime, None]):
        """
        :param player:
            the player questing
        :param quest:
            if not None then it's the quest the player is currently doing, otherwise it means the player is in town
        :param finish_time:
            the time the quest finishes. If None the player is in town
        """
        self.player = player
        self.quest = quest
        self.finish_time = finish_time

    def is_quest_finished(self) -> bool:
        """ returns whether the current quest is finished by checking the finish time """
        return datetime.now() > self.finish_time

    def player_id(self):
        """ non-verbose way to get player id """
        return self.player.player_id

    def quest_id(self):
        """ non-verbose way to get quest id """
        return self.quest.quest_id
