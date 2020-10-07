import random
import string
from io import BytesIO

import aiohttp
import discord
from motor.motor_asyncio import AsyncIOMotorClient
from PIL import Image, ImageDraw, ImageFont, ImageOps
from redbot.core.data_manager import bundled_data_path

import random
import textwrap
from .abc import MixinMeta
from .functions import (
    COMMENT_TYPES,
    FOULS,
    YELLOW_CARDS,
    YC_FOULS,
    YELLOW_CARDS2,
    YC_OFFENSES,
    RED_CARDS,
    RC_FOULS,
    RED_CARDS2,
    RC_OFFENSES,
    CHANCE_TYPE,
    GOAL,
    SAVED_CHANCE,
    MISSED_CHANCE,
    MISSED_DIST,
    BLOCKED_CHANCE,
    DISTANCE,
    HEIGHT,
    SIDE,
)

client = AsyncIOMotorClient()
db = client["leveler"]

DEFAULT_URL = "https://i.imgur.com/pQMaU8U.png"


def list_to_tuple(value):
    return tuple(value) if type(value) == list else value


class SimHelper(MixinMeta):
    async def simpic(
        self,
        ctx,
        time,
        event,
        player,
        team1,
        team2,
        teamevent,
        score1,
        score2,
        assister=None,
        men: int = None,
        penscore1=None,
        penscore2=None,
    ):
        maps = {
            "cornerscore": "GOALLLLL! (CORNER)",
            "cornermiss": "CHANCE MISSED!",
            "goal": "GOALLLLL!",
            "yellow": "YELLOW CARD!",
            "red": "RED CARD! ({} Men!)".format(men),
            "2yellow": "2nd YELLOW! RED!",
            "penscore": "GOALLLLL! (PENALTY)",
            "penmiss": "PENALTY MISSED!",
        }
        theme = await self.config.guild(ctx.guild).theme()
        font_bold_file = f"{bundled_data_path(self)}/font_bold.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        desc_fnt = ImageFont.truetype(font_bold_file, 16)
        header_u_fnt = ImageFont.truetype(font_bold_file, 18)
        general_u_font = ImageFont.truetype(font_bold_file, 15)
        general_info_fnt = ImageFont.truetype(font_bold_file, 15, encoding="utf-8")
        level_label_fnt = ImageFont.truetype(font_bold_file, 22, encoding="utf-8")
        rank_avatar = BytesIO()
        await player.avatar_url.save(rank_avatar, seek_begin=True)
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        if event != "yellow" or event != "goal":
            server_icon = await self.getimg(
                teams[teamevent]["logo"] if teams[teamevent]["logo"] is not None else DEFAULT_URL
            )
        if event == "yellow":
            server_icon = await self.getimg("https://i.imgur.com/wFS9zdd.png")
        if event == "red":
            server_icon = await self.getimg("https://i.imgur.com/2rlT6Ag.png")
        if event == "2yellow":
            server_icon = await self.getimg("https://i.imgur.com/SMZXrVz.jpg")

        profile_image = Image.open(rank_avatar).convert("RGBA")
        try:
            server_icon_image = Image.open(server_icon).convert("RGBA")
        except:
            server_icon = await self.getimg(DEFAULT_URL)
            server_icon_image = Image.open(server_icon).convert("RGBA")

        # set canvas
        width = 360
        if assister is not None:
            height = 120
        else:
            height = 100
        if event == "goal":
            height = height + 30
        bg_color = list_to_tuple(theme["general"]["bg_color"])
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        left_pos = 135
        right_pos = width - vert_pos
        title_height = 22
        gap = 3

        fill = theme["chances"]["header_text_bg"]
        if event in ["penscore", "cornerscore", "goal"]:
            fill = theme["goals"]["header_text_bg"]
        if event in ["penmiss", "cornermiss", "yellow", "red", "2yellow"]:
            fill = theme["fouls"]["header_text_bg"]
        fill = list_to_tuple(fill)

        draw.rectangle(
            [(left_pos - 20, vert_pos), (right_pos, vert_pos + title_height)], fill=fill,
        )  # title box

        content_top = vert_pos + title_height + gap
        content_bottom = 100 - vert_pos

        info_color = (30, 30, 30, 160)

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        circle_left = 15
        circle_top = int((height - lvl_circle_dia) / 2)
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # draws mask
        total_gap = 10
        border = int(total_gap / 2)
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture
        output = ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
        output.resize((profile_size, profile_size), Image.ANTIALIAS)
        mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
        profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
        process.paste(profile_image, (circle_left + border, circle_top + border), mask)

        # put in server picture
        server_size = content_bottom - content_top - 10
        server_border_size = server_size + 4
        radius = 20
        light_border = (150, 150, 150, 180)
        dark_border = (90, 90, 90, 180)
        border_color = self._contrast(info_color, light_border, dark_border)

        draw_server_border = Image.new(
            "RGBA",
            (server_border_size * multiplier, server_border_size * multiplier),
            border_color,
        )
        draw_server_border = self._add_corners(draw_server_border, int(radius * multiplier / 2))
        draw_server_border = draw_server_border.resize(
            (server_border_size, server_border_size), Image.ANTIALIAS
        )
        server_icon_image = server_icon_image.resize(
            (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
        )
        server_icon_image = self._add_corners(server_icon_image, int(radius * multiplier / 2) - 10)
        server_icon_image = server_icon_image.resize((server_size, server_size), Image.ANTIALIAS)
        process.paste(
            draw_server_border,
            (circle_left + profile_size + 2 * border + 8, content_top + 3),
            draw_server_border,
        )
        process.paste(
            server_icon_image,
            (circle_left + profile_size + 2 * border + 10, content_top + 5),
            server_icon_image,
        )

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        # draw level box
        level_left = 290
        level_right = right_pos
        fill = theme["chances"]["header_time_bg"]
        if event in ["penscore", "cornerscore", "goal"]:
            fill = theme["goals"]["header_time_bg"]
        if event in ["yellow", "red", "2yellow"]:
            fill = theme["fouls"]["header_time_bg"]
        fill = list_to_tuple(fill)

        draw.rectangle(
            [(level_left, vert_pos), (level_right, vert_pos + title_height)], fill=fill
        )  # box
        lvl_text = "'" + str(time)
        fill = list_to_tuple(theme["goals"]["header_time_col"])
        draw.text(
            (self._center(level_left, level_right, lvl_text, level_label_fnt), vert_pos + 3),
            lvl_text,
            font=level_label_fnt,
            fill=fill,
        )  # Level #
        left_text_align = 130
        goal_text_color = theme["chances"]["header_text_col"]
        if event in ["penscore", "cornerscore", "goal"]:
            goal_text_color = theme["goals"]["header_text_col"]
        if event in ["yellow", "red", "2yellow"]:
            goal_text_color = theme["fouls"]["header_text_col"]
        goal_text_color = list_to_tuple(goal_text_color)
        # goal text
        _write_unicode(
            maps[event],
            left_text_align - 12,
            vert_pos + 3,
            name_fnt,
            header_u_fnt,
            goal_text_color,
        )
        label_align = 185
        label_text_color = list_to_tuple(theme["goals"]["desc_text_col"])
        goal_comment = None
        if event in ["yellow", "2yellow"]:
            yc = random.choice([YELLOW_CARDS, YELLOW_CARDS2])
            yc = random.randint(0, 1)
            if yc > 0.5:
                yc_foul = random.choice(YC_FOULS)
                yc_text = "yellow card" if event == "yellow" else "2nd yellow card"
                yc_comment = YELLOW_CARDS.format(
                    player.name, teamevent.upper(), yc_foul, assister.name, player.name, yc_text
                )
            else:
                yc_foul = random.choice(YC_OFFENSES)
                yc_text = "yellow card" if event == "yellow" else "2nd yellow card"
                yc_comment = YELLOW_CARDS2.format(player.name, teamevent.upper(), yc_text, yc_foul)
            if event == "2yellow":
                yc_comment += " Red card!!"

        if event == "red":
            rc = random.choice([RED_CARDS, RED_CARDS2])
            rc = random.randint(0, 1)
            if rc > 0.5:
                rc_foul = random.choice(RC_FOULS)
                rc_comment = RED_CARDS.format(
                    player.name, teamevent.upper(), rc_foul, assister.name
                )
            else:
                rc_foul = random.choice(RC_OFFENSES)
                rc_comment = RED_CARDS2.format(player.name, teamevent.upper(), rc_foul)

        if event == "goal":
            gheight = random.choice(HEIGHT)
            gside = random.choice(SIDE)
            gdistance = random.choice(DISTANCE)
            goal_comment = GOAL.format(gdistance, gheight, gside)

        if assister is None:
            draw.text(
                (label_align, 38),
                "Player: {}".format(player.name),
                font=general_u_font,
                fill=label_text_color,
            )
            draw.text(
                (label_align, 58),
                "Team: {}".format(teamevent.upper()),
                font=general_info_fnt,
                fill=label_text_color,
            )
            if penscore1 is not None:
                draw.text(
                    (label_align, 78),
                    "{} {} ({}) : ({}) {} {}".format(
                        team1.upper()[:3], score1, penscore1, penscore2, score2, team2.upper()[:3]
                    ),
                    font=general_info_fnt,
                    fill=label_text_color,
                )
            else:
                draw.text(
                    (label_align, 78),
                    "{} {} : {} {}".format(team1.upper()[:3], score1, score2, team2.upper()[:3]),
                    font=general_info_fnt,
                    fill=label_text_color,
                )
            if goal_comment is not None:
                draw.text(
                    (20, 108),
                    textwrap.fill(goal_comment, 65),
                    font=desc_fnt,
                    fill=label_text_color,
                )
        else:
            if event == "red":
                draw.text(
                    (label_align, 38),
                    textwrap.fill(rc_comment, 28),
                    font=general_info_fnt,
                    fill=label_text_color,
                )
            elif event in ["yellow", "2yellow"]:
                draw.text(
                    (label_align, 38),
                    textwrap.fill(yc_comment, 28),
                    font=general_info_fnt,
                    fill=label_text_color,
                )
            else:
                draw.text(
                    (label_align, 38),
                    "Player: {}".format(player.name),
                    font=general_u_font,
                    fill=label_text_color,
                )
                draw.text(
                    (label_align, 58),
                    "Assisted By: {}".format(assister.name),
                    font=general_info_fnt,
                    fill=label_text_color,
                )
                draw.text(
                    (label_align, 78),
                    "Team: {}".format(teamevent.upper()),
                    font=general_u_font,
                    fill=label_text_color,
                )
                draw.text(
                    (label_align, 98),
                    "{} {} : {} {}".format(team1.upper()[:3], score1, score2, team2.upper()[:3]),
                    font=general_info_fnt,
                    fill=label_text_color,
                )
            if goal_comment is not None:
                draw.text(
                    (20, 123),
                    textwrap.fill(goal_comment, 65),
                    font=desc_fnt,
                    fill=label_text_color,
                )

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="pikaleague.png")
        return image

    def _contrast(self, bg_color, color1, color2):
        color1_ratio = self._contrast_ratio(bg_color, color1)
        color2_ratio = self._contrast_ratio(bg_color, color2)
        if color1_ratio >= color2_ratio:
            return color1
        else:
            return color2

    def _luminance(self, color):
        # convert to greyscale
        luminance = float((0.2126 * color[0]) + (0.7152 * color[1]) + (0.0722 * color[2]))
        return luminance

    def _contrast_ratio(self, bgcolor, foreground):
        f_lum = float(self._luminance(foreground) + 0.05)
        bg_lum = float(self._luminance(bgcolor) + 0.05)

        if bg_lum > f_lum:
            return bg_lum / f_lum
        else:
            return f_lum / bg_lum

    def _add_corners(self, im, rad, multiplier=6):
        raw_length = rad * 2 * multiplier
        circle = Image.new("L", (raw_length, raw_length), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, raw_length, raw_length), fill=255)
        circle = circle.resize((rad * 2, rad * 2), Image.ANTIALIAS)

        alpha = Image.new("L", im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    def _truncate_text(self, text, max_length):
        if len(text) > max_length:
            if text.strip("$").isdigit():
                text = int(text.strip("$"))
                return "${:.2E}".format(text)
            return text[: max_length - 3] + "..."
        return text

    def _center(self, start, end, text, font):
        dist = end - start
        width = font.getsize(text)[0]
        start_pos = start + ((dist - width) / 2)
        return int(start_pos)

    async def timepic(
        self, ctx, team1, team2, score1, score2, time, logo, penscore1=None, penscore2=None
    ):
        font_bold_file = f"{bundled_data_path(self)}/LeagueSpartan-Bold.otf"
        name_fnt = ImageFont.truetype(font_bold_file, 20)
        name_fnt_pen = ImageFont.truetype(font_bold_file, 14)
        # set canvas
        width = 360
        height = 100
        bg_color = (255, 255, 255, 0)
        logos = {
            "bbc": "https://i.imgur.com/eCPpheL.png",
            "bein": "https://i.imgur.com/VTzMuKv.png",
            "sky": "https://i.imgur.com/sdTk0lW.png",
            "bt": "https://i.imgur.com/RFWiSfK.png",
        }
        scorebg = Image.open(await self.getimg(logos[logo]))
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)
        process.paste(scorebg, (0, 0))
        draw = ImageDraw.Draw(process)
        team1 = team1[:3].upper()
        team2 = team2[:3].upper()
        score = f"{score1} - {score2}"
        penscore = f"({penscore1}) pen. ({penscore2})"
        draw.text((115, 40), team1, font=name_fnt, fill=(0, 0, 0, 0))
        draw.text((195, 40), score, font=name_fnt, fill=(255, 255, 255, 255))
        if penscore1 is not None and penscore1 != penscore2:
            draw.text((180, 70), penscore, font=name_fnt_pen, fill=(255, 255, 255, 255))
        draw.text((205, 5), time, font=name_fnt, fill=(255, 255, 255, 255))
        draw.text((295, 40), team2, font=name_fnt, fill=(0, 0, 0, 0))

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="score.png")
        return image

    async def penaltyimg(self, ctx, teamevent, time, player):
        theme = await self.config.guild(ctx.guild).theme()
        font_bold_file = f"{bundled_data_path(self)}/font_bold.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        header_u_fnt = ImageFont.truetype(font_bold_file, 18)
        general_u_font = ImageFont.truetype(font_bold_file, 18)
        general_info_fnt = ImageFont.truetype(font_bold_file, 18, encoding="utf-8")
        level_label_fnt = ImageFont.truetype(font_bold_file, 22, encoding="utf-8")
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        server_icon = await self.getimg(
            teams[teamevent]["logo"] if teams[teamevent]["logo"] is not None else DEFAULT_URL
        )

        try:
            server_icon_image = Image.open(server_icon).convert("RGBA")
        except:
            server_icon = await self.getimg(DEFAULT_URL)
            server_icon_image = Image.open(server_icon).convert("RGBA")

        # set canvas
        width = 360
        height = 100
        bg_color = list_to_tuple(theme["general"]["bg_color"])
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        left_pos = 13
        right_pos = width - vert_pos
        title_height = 22
        gap = 3

        fill = list_to_tuple(theme["chances"]["header_text_bg"])
        draw.rectangle(
            [(left_pos - 10, vert_pos), (right_pos, vert_pos + title_height)], fill=fill,
        )  # title box

        content_top = vert_pos + title_height + gap
        content_bottom = 100 - vert_pos

        info_color = (30, 30, 30, 160)

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # draws mask
        total_gap = 10
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture

        # put in server picture
        server_size = content_bottom - content_top - 10
        server_border_size = server_size + 4
        radius = 20
        light_border = (150, 150, 150, 180)
        dark_border = (90, 90, 90, 180)
        border_color = self._contrast(info_color, light_border, dark_border)

        draw_server_border = Image.new(
            "RGBA",
            (server_border_size * multiplier, server_border_size * multiplier),
            border_color,
        )
        draw_server_border = self._add_corners(draw_server_border, int(radius * multiplier / 2))
        draw_server_border = draw_server_border.resize(
            (server_border_size, server_border_size), Image.ANTIALIAS
        )
        server_icon_image = server_icon_image.resize(
            (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
        )
        server_icon_image = self._add_corners(server_icon_image, int(radius * multiplier / 2) - 10)
        server_icon_image = server_icon_image.resize((server_size, server_size), Image.ANTIALIAS)
        process.paste(draw_server_border, (8, content_top + 3), draw_server_border)
        process.paste(server_icon_image, (10, content_top + 5), server_icon_image)

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        # draw level box
        level_left = 185
        level_right = right_pos
        fill = list_to_tuple(theme["chances"]["header_time_bg"])
        draw.rectangle(
            [(level_left + 5, vert_pos), (level_right, vert_pos + title_height)], fill=fill
        )  # box
        lvl_text = "'" + str(time)
        fill = list_to_tuple(theme["chances"]["header_time_col"])
        draw.text(
            (self._center(level_left, level_right, lvl_text, level_label_fnt), vert_pos + 3),
            lvl_text,
            font=level_label_fnt,
            fill=fill,
        )  # Level #
        left_text_align = 13
        text_color = list_to_tuple(theme["chances"]["header_text_col"])
        # goal text
        _write_unicode(
            "PENALTY!   ({})".format(teamevent[:6].upper()),
            left_text_align - 7,
            vert_pos + 3,
            name_fnt,
            header_u_fnt,
            text_color,
        )
        label_align = 80
        label_text_color = list_to_tuple(theme["chances"]["desc_text_col"])
        draw.text(
            (label_align, 38),
            "Team: {}".format(teamevent.upper()),
            font=general_info_fnt,
            fill=label_text_color,
        )
        draw.text(
            (label_align, 58),
            "{} takes up position to shoot!".format(player.name),
            font=general_u_font,
            fill=label_text_color,
        )

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="pikaleague.png")
        return image

    async def cornerimg(self, ctx, teamevent, time, player):
        theme = await self.config.guild(ctx.guild).theme()
        font_bold_file = f"{bundled_data_path(self)}/font_bold.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        header_u_fnt = ImageFont.truetype(font_bold_file, 18)
        general_u_font = ImageFont.truetype(font_bold_file, 18)
        general_info_fnt = ImageFont.truetype(font_bold_file, 18, encoding="utf-8")
        level_label_fnt = ImageFont.truetype(font_bold_file, 22, encoding="utf-8")
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        server_icon = await self.getimg(
            teams[teamevent]["logo"] if teams[teamevent]["logo"] is not None else DEFAULT_URL
        )

        try:
            server_icon_image = Image.open(server_icon).convert("RGBA")
        except:
            server_icon = await self.getimg(DEFAULT_URL)
            server_icon_image = Image.open(server_icon).convert("RGBA")

        # set canvas
        width = 360
        height = 100
        bg_color = list_to_tuple(theme["general"]["bg_color"])
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        left_pos = 13
        right_pos = width - vert_pos
        title_height = 22
        gap = 3

        fill = list_to_tuple(theme["chances"]["header_text_bg"])
        draw.rectangle(
            [(left_pos - 10, vert_pos), (right_pos, vert_pos + title_height)], fill=fill,
        )  # title box

        content_top = vert_pos + title_height + gap
        content_bottom = 100 - vert_pos

        info_color = (30, 30, 30, 160)

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # draws mask
        total_gap = 10
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture

        # put in server picture
        server_size = content_bottom - content_top - 10
        server_border_size = server_size + 4
        radius = 20
        light_border = (150, 150, 150, 180)
        dark_border = (90, 90, 90, 180)
        border_color = self._contrast(info_color, light_border, dark_border)

        draw_server_border = Image.new(
            "RGBA",
            (server_border_size * multiplier, server_border_size * multiplier),
            border_color,
        )
        draw_server_border = self._add_corners(draw_server_border, int(radius * multiplier / 2))
        draw_server_border = draw_server_border.resize(
            (server_border_size, server_border_size), Image.ANTIALIAS
        )
        server_icon_image = server_icon_image.resize(
            (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
        )
        server_icon_image = self._add_corners(server_icon_image, int(radius * multiplier / 2) - 10)
        server_icon_image = server_icon_image.resize((server_size, server_size), Image.ANTIALIAS)
        process.paste(draw_server_border, (8, content_top + 3), draw_server_border)
        process.paste(server_icon_image, (10, content_top + 5), server_icon_image)

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        # draw level box
        level_left = 185
        level_right = right_pos
        fill = list_to_tuple(theme["chances"]["header_time_bg"])
        draw.rectangle(
            [(level_left, vert_pos), (level_right, vert_pos + title_height)], fill=fill
        )  # box
        lvl_text = "'" + str(time)
        fill = list_to_tuple(theme["chances"]["header_time_col"])
        draw.text(
            (self._center(level_left, level_right, lvl_text, level_label_fnt), vert_pos + 3),
            lvl_text,
            font=level_label_fnt,
            fill=fill,
        )  # Level #
        left_text_align = 13
        text_color = list_to_tuple(theme["chances"]["header_text_col"])
        # goal text
        _write_unicode(
            "CORNER!   ({})".format(teamevent[:6].upper()),
            left_text_align - 7,
            vert_pos + 3,
            name_fnt,
            header_u_fnt,
            text_color,
        )
        label_align = 80
        label_text_color = list_to_tuple(theme["chances"]["desc_text_col"])
        draw.text(
            (label_align, 38),
            "Team: {}".format(teamevent.upper()),
            font=general_info_fnt,
            fill=label_text_color,
        )
        # TODO: Extract this
        corner_comment = random.choice(
            [
                "{} lines up an inswinging corner...",
                "{} lines up an outswinging corner...",
                "{} takes it short...",
            ]
        )
        draw.text(
            (label_align, 58),
            corner_comment.format(player.name),
            font=general_u_font,
            fill=label_text_color,
        )

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="pikaleague.png")
        return image

    async def commentimg(self, ctx, teamevent, time, player, idx=None):
        theme = await self.config.guild(ctx.guild).theme()
        font_bold_file = f"{bundled_data_path(self)}/font_bold.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        header_u_fnt = ImageFont.truetype(font_bold_file, 18)
        general_u_font = ImageFont.truetype(font_bold_file, 18)
        level_label_fnt = ImageFont.truetype(font_bold_file, 22, encoding="utf-8")
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        server_icon = await self.getimg(
            teams[teamevent]["logo"] if teams[teamevent]["logo"] is not None else DEFAULT_URL
        )

        try:
            server_icon_image = Image.open(server_icon).convert("RGBA")
        except:
            server_icon = await self.getimg(DEFAULT_URL)
            server_icon_image = Image.open(server_icon).convert("RGBA")

        # set canvas
        width = 360
        height = 100
        bg_color = list_to_tuple(theme["general"]["bg_color"])
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        left_pos = 13
        right_pos = width - vert_pos
        title_height = 22
        gap = 3

        fill = theme["chances"]["header_text_bg"]
        comment_type = COMMENT_TYPES[idx] if idx is not None else random.choice(COMMENT_TYPES)
        if comment_type == "FOUL!":
            fill = theme["fouls"]["header_text_bg"]
        fill = list_to_tuple(fill)
        draw.rectangle(
            [(left_pos - 10, vert_pos), (right_pos, vert_pos + title_height)], fill=fill
        )  # title box

        content_top = vert_pos + title_height + gap
        content_bottom = 100 - vert_pos

        info_color = (30, 30, 30, 160)

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # draws mask
        total_gap = 10
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture

        # put in server picture
        server_size = content_bottom - content_top - 10
        server_border_size = server_size + 4
        radius = 20
        light_border = (150, 150, 150, 180)
        dark_border = (90, 90, 90, 180)
        border_color = self._contrast(info_color, light_border, dark_border)

        draw_server_border = Image.new(
            "RGBA",
            (server_border_size * multiplier, server_border_size * multiplier),
            border_color,
        )
        draw_server_border = self._add_corners(draw_server_border, int(radius * multiplier / 2))
        draw_server_border = draw_server_border.resize(
            (server_border_size, server_border_size), Image.ANTIALIAS
        )
        server_icon_image = server_icon_image.resize(
            (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
        )
        server_icon_image = self._add_corners(server_icon_image, int(radius * multiplier / 2) - 10)
        server_icon_image = server_icon_image.resize((server_size, server_size), Image.ANTIALIAS)
        process.paste(draw_server_border, (8, content_top + 3), draw_server_border)
        process.paste(server_icon_image, (10, content_top + 5), server_icon_image)

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        # draw level box
        level_left = 185
        level_right = right_pos
        fill = theme["chances"]["header_time_bg"]
        if comment_type == "FOUL!":
            fill = theme["fouls"]["header_time_bg"]
        fill = list_to_tuple(fill)
        draw.rectangle(
            [(level_left + 5, vert_pos), (level_right, vert_pos + title_height)], fill=fill
        )  # box
        lvl_text = "'" + str(time)
        fill = theme["chances"]["header_time_col"]
        if comment_type == "FOUL!":
            fill = theme["fouls"]["header_time_col"]
        fill = list_to_tuple(fill)
        draw.text(
            (self._center(level_left, level_right, lvl_text, level_label_fnt), vert_pos + 3),
            lvl_text,
            font=level_label_fnt,
            fill=fill,
        )  # Level #
        left_text_align = 13
        text_color = theme["chances"]["header_text_col"]
        if comment_type == "FOUL!":
            text_color = theme["fouls"]["header_text_col"]
        text_color = list_to_tuple(text_color)
        # goal text
        comment = ""
        if comment_type == "FOUL!":
            comment = random.choice(FOULS).format(player.name, teamevent[:6].upper())
        else:
            height = random.choice(HEIGHT)
            side = random.choice(SIDE)
            distance = random.choice(DISTANCE)
            missed_dist = random.choice(MISSED_DIST)

            chance_type = random.choice(CHANCE_TYPE)
            if chance_type == "saved":
                comment = SAVED_CHANCE.format(
                    player.name, teamevent[:6].upper(), distance, height, side
                )
            elif chance_type == "missed":
                comment = MISSED_CHANCE.format(
                    player.name, teamevent[:6].upper(), distance, missed_dist
                )
            else:
                comment = BLOCKED_CHANCE.format(player.name, teamevent[:6].upper(), distance)

        _write_unicode(
            comment_type + "   ({})".format(teamevent[:6].upper()),
            left_text_align - 7,
            vert_pos + 3,
            name_fnt,
            header_u_fnt,
            text_color,
        )
        label_align = 80
        label_text_color = theme["chances"]["desc_text_col"]
        if comment_type == "FOUL!":
            label_text_color = theme["fouls"]["desc_text_col"]
        label_text_color = list_to_tuple(label_text_color)

        draw.text(
            (label_align, 38),
            textwrap.fill(comment, 45),
            font=general_u_font,
            fill=label_text_color,
        )
        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="commentary.png")
        return image

    async def extratime(self, ctx, time):
        time = str(time)
        font_bold_file = f"{bundled_data_path(self)}/LeagueSpartan-Bold.otf"
        svn = f"{bundled_data_path(self)}/Seven-Segment.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 20)
        name_fnt2 = ImageFont.truetype(svn, 160)
        name_fnt3 = ImageFont.truetype(svn, 100)
        # set canvas
        width = 745
        height = 387
        bg_color = (255, 255, 255, 0)
        scorebg = Image.open(await self.getimg("https://i.imgur.com/k8U1wdt.png"))
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)
        process.paste(scorebg, (0, 0))
        draw = ImageDraw.Draw(process)
        if time == "1":
            draw.text((360, 90), time, font=name_fnt2, fill=(255, 0, 0, 255))
        elif time == "15":
            draw.text((130, 130), "EXTRA TIME", font=name_fnt3, fill=(255, 0, 0, 255))
        else:
            draw.text((330, 90), time, font=name_fnt2, fill=(255, 0, 0, 255))
        if time != "15":
            draw.text(
                (290, 295), f"{time} added minute(s)", font=name_fnt, fill=(255, 255, 255, 255)
            )

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="extratime.png")
        return image

    async def motmpic(self, ctx, user, team, goals, assists):
        theme = await self.config.guild(ctx.guild).theme()
        font_bold_file = f"{bundled_data_path(self)}/font_bold.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        general_info_fnt = ImageFont.truetype(font_bold_file, 15, encoding="utf-8")
        header_u_fnt = ImageFont.truetype(font_bold_file, 18)
        rank_avatar = BytesIO()
        await user.avatar_url.save(rank_avatar, seek_begin=True)
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        server_icon = await self.getimg(
            teams[team]["logo"] if teams[team]["logo"] is not None else DEFAULT_URL
        )

        profile_image = Image.open(rank_avatar).convert("RGBA")
        try:
            server_icon_image = Image.open(server_icon).convert("RGBA")
        except:
            server_icon = await self.getimg(DEFAULT_URL)
            server_icon_image = Image.open(server_icon).convert("RGBA")

        # set canvas
        width = 300
        height = 100
        bg_color = list_to_tuple(theme["general"]["bg_color"])
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        left_pos = 135
        right_pos = width - vert_pos
        title_height = 22
        gap = 3

        fill = list_to_tuple(theme["chances"]["header_text_bg"])
        draw.rectangle(
            [(left_pos - 20, vert_pos), (right_pos, vert_pos + title_height)], fill=fill,
        )  # title box

        content_top = vert_pos + title_height + gap
        content_bottom = 100 - vert_pos

        info_color = (30, 30, 30, 160)

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        circle_left = 15
        circle_top = int((height - lvl_circle_dia) / 2)
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # draws mask
        total_gap = 10
        border = int(total_gap / 2)
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        # put in profile picture
        output = ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
        output.resize((profile_size, profile_size), Image.ANTIALIAS)
        mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
        profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
        process.paste(profile_image, (circle_left + border, circle_top + border), mask)

        # put in server picture
        server_size = content_bottom - content_top - 10
        server_border_size = server_size + 4
        radius = 20
        light_border = (150, 150, 150, 180)
        dark_border = (90, 90, 90, 180)
        border_color = self._contrast(info_color, light_border, dark_border)

        draw_server_border = Image.new(
            "RGBA",
            (server_border_size * multiplier, server_border_size * multiplier),
            border_color,
        )
        draw_server_border = self._add_corners(draw_server_border, int(radius * multiplier / 2))
        draw_server_border = draw_server_border.resize(
            (server_border_size, server_border_size), Image.ANTIALIAS
        )
        server_icon_image = server_icon_image.resize(
            (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
        )
        server_icon_image = self._add_corners(server_icon_image, int(radius * multiplier / 2) - 10)
        server_icon_image = server_icon_image.resize((server_size, server_size), Image.ANTIALIAS)
        process.paste(
            draw_server_border,
            (circle_left + profile_size + 2 * border + 8, content_top + 3),
            draw_server_border,
        )
        process.paste(
            server_icon_image,
            (circle_left + profile_size + 2 * border + 10, content_top + 5),
            server_icon_image,
        )

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        left_text_align = 130
        text_color = list_to_tuple(theme["chances"]["header_text_col"])
        # goal text
        name = user.name
        if len(name) > 15:
            name = name[:13] + "..."
        _write_unicode(
            "MOTM: {}".format(name),
            left_text_align - 7,
            vert_pos + 3,
            name_fnt,
            header_u_fnt,
            text_color,
        )
        label_align = 185
        label_text_color = list_to_tuple(theme["chances"]["desc_text_col"])
        draw.text(
            (label_align, 38),
            "Team: {}".format(self._truncate_text(team, 10)),
            font=general_info_fnt,
            fill=label_text_color,
        )
        draw.text(
            (label_align, 58),
            "Goals: {}".format(goals),
            font=general_info_fnt,
            fill=label_text_color,
        )
        draw.text(
            (label_align, 78),
            "Assists: {}".format(assists),
            font=general_info_fnt,
            fill=label_text_color,
        )

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="pikaleague.png")
        return image

    async def walkout(self, ctx, team1, home_or_away):
        theme = await self.config.guild(ctx.guild).theme()
        font_bold_file = f"{bundled_data_path(self)}/font_bold.ttf"
        name_fnt = ImageFont.truetype(font_bold_file, 22)
        header_u_fnt = ImageFont.truetype(font_bold_file, 18)
        general_u_fnt = ImageFont.truetype(font_bold_file, 15)
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        teamplayers = len(teams[team1]["members"])
        # set canvas
        if teams[team1]["kits"][home_or_away] is None:
            width = 105 * teamplayers
        else:
            width = (105 * teamplayers) + 150
        height = 200
        bg_color = list_to_tuple(theme["general"]["bg_color"])
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)

        # draw
        draw = ImageDraw.Draw(process)

        # draw transparent overlay
        vert_pos = 5
        right_pos = width - vert_pos
        title_height = 22

        fill = list_to_tuple(theme["chances"]["header_text_bg"])
        draw.rectangle(
            [(5, vert_pos), (right_pos, vert_pos + title_height)], fill=fill
        )  # title box

        # draw level circle
        multiplier = 6
        lvl_circle_dia = 94
        circle_left = 15
        circle_top = int((height - lvl_circle_dia) / 2)
        raw_length = lvl_circle_dia * multiplier

        # create mask
        mask = Image.new("L", (raw_length, raw_length), 0)
        draw_thumb = ImageDraw.Draw(mask)
        draw_thumb.ellipse((0, 0) + (raw_length, raw_length), fill=255, outline=0)

        # draws mask
        total_gap = 10
        border = int(total_gap / 2)
        profile_size = lvl_circle_dia - total_gap
        raw_length = profile_size * multiplier
        x = 40
        for player in teams[team1]["members"]:
            player = await self.bot.fetch_user(player)
            rank_avatar = BytesIO()
            await player.avatar_url.save(rank_avatar, seek_begin=True)
            profile_image = Image.open(rank_avatar).convert("RGBA")
            # put in profile picture
            output = ImageOps.fit(profile_image, (raw_length, raw_length), centering=(0.5, 0.5))
            output.resize((profile_size, profile_size), Image.ANTIALIAS)
            mask = mask.resize((profile_size, profile_size), Image.ANTIALIAS)
            profile_image = profile_image.resize((profile_size, profile_size), Image.ANTIALIAS)
            process.paste(profile_image, (circle_left + border, circle_top + border), mask)
            circle_left += 90
            if len(player.name) > 7:
                name = player.name[:6] + "..."
            else:
                name = player.name
            text_color = list_to_tuple(theme["walkout"]["name_text"])
            draw.text((x, 160), name, font=general_u_fnt, fill=text_color)
            x += 90

        def _write_unicode(text, init_x, y, font, unicode_font, fill):
            write_pos = init_x

            for char in text:
                if char.isalnum() or char in string.punctuation or char in string.whitespace:
                    draw.text((write_pos, y), char, font=font, fill=fill)
                    write_pos += font.getsize(char)[0]
                else:
                    draw.text((write_pos, y), "{}".format(char), font=unicode_font, fill=fill)
                    write_pos += unicode_font.getsize(char)[0]

        text_color = list_to_tuple(theme["chances"]["header_text_col"])
        level = teams[team1]["cachedlevel"]
        teamname = self._truncate_text(team1, 10)
        bonus = teams[team1]["bonus"] * 15
        _write_unicode(
            "Team: {} | Total Level: {} | Bonus %: {}".format(teamname, level, bonus),
            10,
            vert_pos + 3,
            name_fnt,
            header_u_fnt,
            text_color,
        )
        if teams[team1]["kits"][home_or_away] is not None:
            vert_pos = 5
            right_pos = width - vert_pos
            title_height = 22
            gap = 3

            content_top = vert_pos + title_height + gap
            content_bottom = 100 - vert_pos
            info_color = (30, 30, 30, 160)
            server_icon = await self.getimg(teams[team1]["kits"][home_or_away])
            server_icon_image = Image.open(server_icon).convert("RGBA")
            server_size = content_bottom - content_top - 10
            server_border_size = server_size + 4
            radius = 20
            light_border = (150, 150, 150, 180)
            dark_border = (90, 90, 90, 180)
            border_color = self._contrast(info_color, light_border, dark_border)

            draw_server_border = Image.new(
                "RGBA",
                (server_border_size * multiplier, server_border_size * multiplier),
                border_color,
            )
            draw_server_border = self._add_corners(
                draw_server_border, int(radius * multiplier / 2)
            )
            draw_server_border = draw_server_border.resize((140, 140), Image.ANTIALIAS)
            server_icon_image = server_icon_image.resize(
                (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
            )
            server_icon_image = self._add_corners(
                server_icon_image, int(radius * multiplier / 2) - 10
            )
            server_icon_image = server_icon_image.resize((136, 136), Image.ANTIALIAS)
            process.paste(draw_server_border, (x, 45), draw_server_border)
            process.paste(server_icon_image, (x + 2, 47), server_icon_image)

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="pikaleague.png")
        return image

    async def matchinfo(self, ctx, teamlist, weather, stadium, homeodds, awayodds, drawodds):
        width = 500
        height = 160
        theme = await self.config.guild(ctx.guild).theme()
        bg_color = list_to_tuple(theme["general"]["bg_color"])
        result = Image.new("RGBA", (width, height), bg_color)
        process = Image.new("RGBA", (width, height), bg_color)
        draw = ImageDraw.Draw(process)

        font_bold_file = f"{bundled_data_path(self)}/font_bold.ttf"
        general_info_fnt = ImageFont.truetype(font_bold_file, 18, encoding="utf-8")
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        level_label_fnt = ImageFont.truetype(font_bold_file, 22, encoding="utf-8")
        level_label_fnt2 = ImageFont.truetype(font_bold_file, 18, encoding="utf-8")
        x = 10
        for team in teamlist:
            server_icon = await self.getimg(
                teams[team]["logo"] if teams[team]["logo"] is not None else DEFAULT_URL
            )
            try:
                server_icon_image = Image.open(server_icon).convert("RGBA")
            except:
                server_icon = await self.getimg(
                    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/A_blank_black_picture.jpg/1536px-A_blank_black_picture.jpg"
                )
                server_icon_image = Image.open(server_icon).convert("RGBA")
            vert_pos = 5
            # draw level circle
            multiplier = 6
            title_height = 22
            gap = 3
            content_top = vert_pos + title_height + gap
            content_bottom = 100 - vert_pos
            # put in server picture
            server_size = content_bottom - content_top - 10
            server_border_size = server_size + 4
            radius = 20
            light_border = (150, 150, 150, 180)
            dark_border = (90, 90, 90, 180)
            info_color = (30, 30, 30, 160)
            border_color = self._contrast(info_color, light_border, dark_border)

            draw_server_border = Image.new(
                "RGBA",
                (server_border_size * multiplier, server_border_size * multiplier),
                border_color,
            )
            draw_server_border = self._add_corners(
                draw_server_border, int(radius * multiplier / 2)
            )
            draw_server_border = draw_server_border.resize(
                (server_border_size, server_border_size), Image.ANTIALIAS
            )
            server_icon_image = server_icon_image.resize(
                (server_size * multiplier, server_size * multiplier), Image.ANTIALIAS
            )
            server_icon_image = self._add_corners(
                server_icon_image, int(radius * multiplier / 2) - 10
            )
            server_icon_image = server_icon_image.resize(
                (server_size, server_size), Image.ANTIALIAS
            )
            process.paste(draw_server_border, (x + 8, content_top + 12), draw_server_border)
            process.paste(server_icon_image, (x + 10, content_top + 14), server_icon_image)
            x += 390

        teamtext_color = list_to_tuple(theme["matchinfo"]["vs_title"])
        teamtext = f"{teamlist[0][:15]} vs {teamlist[1][:15]}"
        homeaway_fill = list_to_tuple(theme["matchinfo"]["home_away_text"])
        draw.text((10, 20), "HOME TEAM:", font=level_label_fnt, fill=homeaway_fill)
        draw.text((400, 20), "AWAY TEAM:", font=level_label_fnt, fill=homeaway_fill)
        draw.text(
            (self._center(0, width, teamtext, level_label_fnt), 20),
            teamtext,
            font=level_label_fnt,
            fill=teamtext_color,
        )
        if stadium is not None:
            stadiumtxt = stadium + " - " + weather
            fill = list_to_tuple(theme["matchinfo"]["stadium"])
            draw.text(
                (self._center(0, width, stadiumtxt, level_label_fnt2), 70),
                stadiumtxt,
                font=level_label_fnt2,
                fill=fill,
            )
        teammembers = list(teams[teamlist[0]]["members"].keys()) + list(
            teams[teamlist[1]]["members"].keys()
        )
        commentator = "Commentator: " + random.choice(
            [x.name for x in ctx.guild.members if x.id not in teammembers and len(x.name) < 25]
        )
        fill = list_to_tuple(theme["matchinfo"]["commentator"])
        draw.text(
            (self._center(0, width, commentator, level_label_fnt2), 45),
            commentator,
            font=level_label_fnt2,
            fill=fill,
        )

        fill = list_to_tuple(theme["matchinfo"]["odds"])
        # odds
        draw.text(
            (10, 120), f"HOME ODDS:\n{str(homeodds)[:7]}", font=general_info_fnt, fill=fill,
        )
        draw.text(
            (400, 120), f"AWAY ODDS:\n{str(awayodds)[:7]}", font=general_info_fnt, fill=fill,
        )
        draw.text(
            (self._center(0, width, f"Draw:", general_info_fnt), 120),
            f"Draw:",
            font=general_info_fnt,
            fill=fill,
        )
        draw.text(
            (self._center(0, width, str(drawodds)[:7], general_info_fnt), 137),
            str(drawodds)[:7],
            font=general_info_fnt,
            fill=fill,
        )

        result = Image.alpha_composite(result, process)
        file = BytesIO()
        result.save(file, "PNG", quality=100)
        file.seek(0)
        image = discord.File(file, filename="pikaleague.png")
        return image

    async def get(self, url):
        async with self.session.get(url) as response:
            resp = await response.json(content_type=None)
            return resp

    async def getimg(self, img):
        async with self.session.get(img) as response:
            if response.status == 200:
                try:
                    buffer = BytesIO(await response.read())
                except aiohttp.ClientPayloadError:
                    async with self.session.get(DEFAULT_URL) as response:
                        buffer = BytesIO(await response.read())
                buffer.name = "picture.png"
                return buffer
            async with self.session.get(DEFAULT_URL) as response:
                buffer = BytesIO(await response.read())
                buffer.name = "picture.png"
                return buffer

    async def addrole(self, ctx, user, role_obj):
        if role_obj is not None:
            member = ctx.guild.get_member(user)
            if member is not None:
                try:
                    await member.add_roles(role_obj)
                except discord.Forbidden:
                    self.log.info("Failed to remove role from {}".format(member.name))

    async def matchnotif(self, ctx, team1, team2):
        cog = self.bot.get_cog("SimLeague")
        teams = await cog.config.guild(ctx.guild).teams()
        mentions = await cog.config.guild(ctx.guild).mentions()
        teamone = list(teams[team1]["members"].keys())
        teamtwo = list(teams[team2]["members"].keys())
        role1 = False
        role2 = False
        msg = ""
        if teams[team1]["role"] and mentions:
            role_obj = ctx.guild.get_role(teams[team1]["role"])
            if role_obj is not None:
                await role_obj.edit(mentionable=True)
                msg += role_obj.mention
                role1 = True
                roleone = role_obj
                mem1 = []
                for memberid in teamone:
                    member = ctx.guild.get_member(memberid)
                    if member is not None:
                        notif = await cog.config.user(member).notify()
                        if role_obj in member.roles:
                            try:
                                if not notif:
                                    await member.remove_roles(role_obj)
                                    mem1.append(member.id)
                            except discord.Forbidden:
                                self.log.info("Failed to remove role from {}".format(member.name))
        else:
            msg += team1
        msg += " VS "
        if teams[team2]["role"] and mentions:
            role_obj = ctx.guild.get_role(teams[team2]["role"])
            if role_obj is not None:
                await role_obj.edit(mentionable=True)
                msg += role_obj.mention
                role2 = True
                roletwo = role_obj
                mem2 = []
                for memberid in teamtwo:
                    member = ctx.guild.get_member(memberid)
                    if member is not None:
                        notif = await cog.config.user(member).notify()
                        if role_obj in member.roles:
                            try:
                                if not notif:
                                    await member.remove_roles(role_obj)
                                    mem2.append(member.id)
                            except discord.Forbidden:
                                self.log.info("Failed to remove role from {}".format(member.name))
        else:
            msg += team2
        await ctx.send(msg)
        if role1:
            await roleone.edit(mentionable=False)
            if mem1:
                for memberid in mem1:
                    member = ctx.guild.get_member(memberid)
                    if member is not None:
                        try:
                            await member.add_roles(roleone)
                        except discord.Forbidden:
                            self.log.info("Failed to remove role from {}".format(member.name))
        if role2:
            await roletwo.edit(mentionable=False)
            if mem2:
                for memberid in mem2:
                    member = ctx.guild.get_member(memberid)
                    if member is not None:
                        try:
                            await member.add_roles(roletwo)
                        except discord.Forbidden:
                            self.log.info("Failed to remove role from {}".format(member.name))

    async def postresults(self, ctx, team1, team2, score1, score2, penscore1=None, penscore2=None):
        cog = self.bot.get_cog("SimLeague")
        results = await cog.config.guild(ctx.guild).resultchannel()
        role1 = False
        role2 = False
        if results:
            result = ""
            teams = await cog.config.guild(ctx.guild).teams()
            teamone = teams[team1]["members"]
            teamtwo = teams[team2]["members"]
            if teams[team1]["role"]:
                role_obj = ctx.guild.get_role(teams[team1]["role"])
                if role_obj is not None:
                    await role_obj.edit(mentionable=True)
                    result += role_obj.mention
                    role1 = True
                    roleone = role_obj
                    mem1 = []
                    for memberid in teamone:
                        member = ctx.guild.get_member(memberid)
                        if member is not None:
                            notif = await cog.config.user(member).notify()
                            if role_obj in member.roles:
                                try:
                                    if not notif:
                                        await member.remove_roles(role_obj)
                                        mem1.append(member.id)
                                except discord.Forbidden:
                                    self.log.info(
                                        "Failed to remove role from {}".format(member.name)
                                    )
            else:
                result += team1
            if penscore1 is not None and penscore1 != penscore2:
                if penscore1 > penscore2:
                    result += f" {score1} **({penscore1})**:({penscore2}) {score2} "
                else:
                    result += f" {score1} ({penscore1}):**({penscore2})** {score2} "
            else:
                if score1 > score2:
                    result += f" **{score1}**:{score2} "
                elif score1 < score2:
                    result += f" {score1}:**{score2}** "
                else:
                    result += f" {score1}:{score2} "
            if teams[team2]["role"]:
                role_obj = ctx.guild.get_role(teams[team2]["role"])
                if role_obj is not None:
                    await role_obj.edit(mentionable=True)
                    result += role_obj.mention
                    role2 = True
                    roletwo = role_obj
                    mem2 = []
                    for memberid in teamtwo:
                        member = ctx.guild.get_member(memberid)
                        if member is not None:
                            notif = await cog.config.user(member).notify()
                            if role_obj in member.roles:
                                try:
                                    if not notif:
                                        await member.remove_roles(role_obj)
                                        mem2.append(member.id)
                                except discord.Forbidden:
                                    self.log.info(
                                        "Failed to remove role from {}".format(member.name)
                                    )
            else:
                result += team2
            for channel in results:
                channel = self.bot.get_channel(channel)
                if channel is not None:
                    await channel.send(result)
            if role1:
                role_obj = ctx.guild.get_role(teams[team1]["role"])
                if role_obj is not None:
                    await role_obj.edit(mentionable=False)
                    if mem1:
                        for memberid in mem1:
                            member = ctx.guild.get_member(memberid)
                            if member is not None:
                                try:
                                    await member.add_roles(roleone)
                                except discord.Forbidden:
                                    self.log.info(
                                        "Failed to remove role from {}".format(member.name)
                                    )

            if role2:
                role_obj = ctx.guild.get_role(teams[team2]["role"])
                if role_obj is not None:
                    await role_obj.edit(mentionable=False)
                    if mem2:
                        for memberid in mem2:
                            member = ctx.guild.get_member(memberid)
                            if member is not None:
                                try:
                                    await member.add_roles(roletwo)
                                except discord.Forbidden:
                                    self.log.info(
                                        "Failed to remove role from {}".format(member.name)
                                    )

    async def posttransfer(self, ctx, title, member1, fromteam, toteam):
        embed = discord.Embed(color=0xCCFFCC)
        embed.title = title
        embed.set_thumbnail(url=member1.avatar_url)
        embed.description = f"{member1.name}\n"
        embed.description += f"**From**: {fromteam}\n"
        embed.description += f"**To**: {toteam}\n"
        cog = self.bot.get_cog("SimLeague")

        transferchannels = await cog.config.guild(ctx.guild).transferchannel()
        if transferchannels:
            for channel in transferchannels:
                channel = self.bot.get_channel(channel)
                if channel is not None:
                    await channel.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    async def yCardChance(self, guild, probability):
        rdmint = random.randint(0, 100)
        if rdmint > probability["yellowchance"]:  # 98 default
            return True

    async def rCardChance(self, guild, probability):
        rdmint = random.randint(0, 400)
        if rdmint > probability["redchance"]:  # 398 default
            return True

    async def goalChance(self, guild, probability):
        rdmint = random.randint(0, 100)
        if rdmint > probability["goalchance"]:  # 96 default
            return True

    async def cornerChance(self, guild, probability):
        rdmint = random.randint(0, 100)
        if rdmint > probability["cornerchance"]:  # 98 default
            return True

    async def cornerBlock(self, guild, probability):
        rdmint = random.randint(0, 1)
        if rdmint > probability["cornerblock"]:  # 0.2 default
            return True

    async def penaltyChance(self, guild, probability):
        rdmint = random.randint(0, 250)
        if rdmint > probability["penaltychance"]:  # 249 probability
            return True

    async def penaltyBlock(self, guild, probability):
        rdmint = random.randint(0, 1)
        if rdmint > probability["penaltyblock"]:  # 0.75 default
            return True

    async def commentChance(self, guild, probability):
        rdmint = random.randint(0, 100)
        if rdmint > probability["commentchance"]:  # 85 probability
            return True

    async def updatecacheall(self, guild):
        self.log.info("Updating global cache.")
        cog = self.bot.get_cog("SimLeague")
        async with cog.config.guild(guild).teams() as teams:
            for team in teams:
                t1totalxp = 0
                teams[team]
                team1pl = teams[team]["members"]

                for memberid in team1pl:
                    user = await self.bot.fetch_user(int(memberid))
                    try:
                        userinfo = await db.users.find_one({"user_id": str(user.id)})
                        level = userinfo["servers"][str(guild.id)]["level"]
                        t1totalxp += int(level) if int(level) > 0 else 1
                    except (KeyError, TypeError):
                        t1totalxp += 1
                teams[team]["cachedlevel"] = t1totalxp

    async def updatecachegame(self, guild, team1, team2):
        self.log.info("Updating game cache.")
        t1totalxp = 0
        t2totalxp = 0
        cog = self.bot.get_cog("SimLeague")
        async with cog.config.guild(guild).teams() as teams:
            team1pl = teams[team1]["members"]

            for memberid in team1pl:
                user = await self.bot.fetch_user(int(memberid))
                try:
                    userinfo = await db.users.find_one({"user_id": str(user.id)})
                    level = userinfo["servers"][str(guild.id)]["level"]
                    t1totalxp += int(level) if int(level) > 0 else 1
                except (KeyError, TypeError):
                    t1totalxp += 1
            teams[team1]["cachedlevel"] = t1totalxp

            team2pl = teams[team2]["members"]
            for memberid in team2pl:
                user = await self.bot.fetch_user(int(memberid))
                try:
                    userinfo = await db.users.find_one({"user_id": str(user.id)})
                    level = userinfo["servers"][str(guild.id)]["level"]
                    t2totalxp += int(level) if int(level) > 0 else 1
                except (KeyError, TypeError):
                    t2totalxp += 1
            teams[team2]["cachedlevel"] = t2totalxp

    async def setnextteam(self, ctx, transfers, team):
        # Set next team as ready to make transfers
        standings = await self.config.guild(ctx.guild).standings()
        teams = await self.config.guild(ctx.guild).teams()
        sortedstandings = sorted(
            standings,
            key=lambda team: (
                standings[team]["points"],
                standings[team]["gd"],
                standings[team]["gf"],
            ),
            reverse=False,
        )
        currentteamindex = sortedstandings.index(team)
        transfers[sortedstandings[currentteamindex]]["ready"] = False
        currentteam = ctx.guild.get_role(teams[sortedstandings[currentteamindex]]["role"]).mention
        if currentteamindex < len(sortedstandings) - 1:
            transfers[sortedstandings[currentteamindex + 1]]["ready"] = True
            nextteam = ctx.guild.get_role(
                teams[sortedstandings[currentteamindex + 1]]["role"]
            ).mention
            await ctx.send("Transfers done for {}, now turn for: {}".format(currentteam, nextteam))
        else:
            await ctx.send("Transfers done for {}".format(currentteam))

    async def swap(
        self, ctx, guild, team1, member1: discord.Member, team2, member2: discord.Member
    ):
        cog = self.bot.get_cog("SimLeague")
        async with cog.config.guild(guild).teams() as teams:
            role1 = guild.get_role(teams[team1]["role"])
            role2 = guild.get_role(teams[team2]["role"])
            if role1 is not None:
                await member1.remove_roles(role1, reason=f"Transfer from {team1} to {team2}")
                await member1.add_roles(role2, reason=f"Transfer from {team1} to {team2}")
            if role2 is not None:
                await member2.add_roles(role1, reason=f"Transfer from {team2} to {team1}")
                await member2.remove_roles(role2, reason=f"Transfer from {team2} to {team1}")

            if str(member1.id) not in teams[team1]["members"]:
                return await ctx.send(f"{member1.name} is not on {team1}.")
            if str(member2.id) not in teams[team2]["members"]:
                return await ctx.send(f"{member2.name} is not on {team2}.")
            if str(member1.id) in teams[team1]["captain"]:
                teams[team1]["captain"] = {}
                teams[team1]["captain"][str(member2.id)] = member2.name
            if str(member2.id) in teams[team2]["captain"]:
                teams[team2]["captain"] = {}
                teams[team2]["captain"][str(member1.id)] = member1.name
            async with self.config.guild(ctx.guild).transfers() as transfers:
                transfers[team1]["swap"] = {"in": member2.name, "out": member1.name}
                await self.setnextteam(ctx, transfers, team1)

            async with self.config.guild(ctx.guild).transferred() as transferred:
                transferred.append(member2.id)

            teams[team1]["members"][str(member2.id)] = member2.name
            del teams[team1]["members"][str(member1.id)]
            teams[team2]["members"][str(member1.id)] = member1.name
            del teams[team2]["members"][str(member2.id)]

            await self.posttransfer(ctx, "New transfer!", member1, team1, team2)
            await self.posttransfer(ctx, "New transfer!", member2, team2, team1)

    async def sign(self, ctx, guild, team1, member1: discord.Member, member2: discord.Member):
        cog = self.bot.get_cog("SimLeague")
        users = await cog.config.guild(guild).users()
        if member2.id in users:
            return await ctx.send("User is currently not a free agent.")
        async with cog.config.guild(guild).teams() as teams:
            role = guild.get_role(teams[team1]["role"])
            if role is not None:
                await member1.remove_roles(role, reason=f"Released from {team1}")
                await member2.add_roles(role, reason=f"Signed for {team1}")

            if str(member1.id) not in teams[team1]["members"]:
                return await ctx.send(f"{member1.name} is not on {team1}.")
            if str(member1.id) in teams[team1]["captain"]:
                teams[team1]["captain"] = {}
                teams[team1]["captain"] = {str(member2.id): member2.name}
            async with self.config.guild(ctx.guild).transfers() as transfers:
                transfers[team1]["sign"] = {"in": member2.name, "out": member1.name}
                await self.setnextteam(ctx, transfers, team1)

            async with self.config.guild(ctx.guild).transferred() as transferred:
                transferred.append(member2.id)
            teams[team1]["members"][str(member2.id)] = member2.name
            del teams[team1]["members"][str(member1.id)]
        async with cog.config.guild(guild).users() as users:
            users.remove(str(member1.id))
            users.append(str(member2.id))

        await self.posttransfer(ctx, "Player released!", member1, team1, "(free agent)")
        await self.posttransfer(ctx, "New signing!!", member2, "(free agent)", team1)

    async def team_delete(self, ctx, team):
        cog = self.bot.get_cog("SimLeague")
        async with cog.config.guild(ctx.guild).teams() as teams:
            if teams[team]["role"] is not None:
                role = ctx.guild.get_role(teams[team]["role"])
                if role is not None:
                    await role.delete()
            if team not in teams:
                return await ctx.send("Team was not found, ensure capitilization is correct.")
            async with cog.config.guild(ctx.guild).users() as users:
                for uid in teams[team]["members"]:
                    user = ctx.guild.get_member(int(uid))
                    cptrole = [r for r in user.roles if r.name == "Sim Captain"][0]
                    if cptrole:
                        await user.remove_roles(cptrole)
                    users.remove(uid)
            del teams[team]
            async with cog.config.guild(ctx.guild).standings() as standings:
                del standings[team]
            return await ctx.send("Team successfully removed.")
