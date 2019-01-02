from nxtools import *
from nxtools.caspar import *

import copy

LIVE = -1


__all__ = ["get_info_parser"]

class BaseInfoParser(object):
    def __init__(self, caspar, channel, default_fps=25.0):
        self.caspar = caspar
        self.channel = channel
        self.data = None
        self._seek_fps = None

        self.default_fps = default_fps

        self.defaults = {
                "current" : False,
                "cued" : False,
                "pos" : 0,
                "dur" : 0
            }

    @property
    def seek_fps(self):
        if self._seek_fps is None:
            self._seek_fps = self.load_seek_fps()
        return self._seek_fps

    def refresh(self):
        response = self.caspar.query("INFO {}".format(self.channel))
        if response.is_error:
            self.data = None
        else:
            try:
                self.data = xml(response.data)
            except Exception:
                log_traceback
                self.data = None

    def load_seek_fps(self):
        return self.default_fps

    def get_info(self, layer_index=10, refresh=True):
        if refresh:
            self.refresh()
        if not self.data:
            return None
        result = self.parse(layer_index)
        return result or self.defaults




class Caspar207InfoParser(BaseInfoParser):
    def parse(self, layer_index):
        return None


class Caspar21InfoParser(BaseInfoParser):
    def parse(self, layer_index):
        return None



class Caspar22InfoParser(BaseInfoParser):
    def load_seek_fps(self):
        self.refresh()
        frates = self.data.findall("framerate")
        if not len(frates) == 2:
            return False
        fpsn = int(frates[0].text)
        fpsd = int(frates[1].text)
        return fpsn/fpsd

    def parse(self, layer_index):
        try:
            layers = self.data.find("stage").find("layer")
        except:
            return None

        feed_layer = None
        for layer in layers:
            ltag = layer.tag.split("_")
            if len(ltag) == 2 and ltag[0] == "layer" and ltag[1] == str(layer_index):
                feed_layer = layer
                break
        else:
            return None

        data = copy.deepcopy(self.defaults)

        bg = feed_layer.find("background")
        bg_producer = bg.find("producer").text
        if bg_producer == "empty":
            data["cued"] = False
        elif bg_producer in ["ffmpeg", "transition"]:
            data["cued"] = get_base_name(bg.find("file").find("path").text)
        else:
            data["cued"] = LIVE

        fg = feed_layer.find("foreground")
        fg_producer = fg.find("producer").text
        if fg_producer == "empty":
            data["current"] = False
        elif fg_producer in ["ffmpeg", "transition"]:
            f = fg.find("file")
            data["current"] = get_base_name(f.find("path").text)

            #fps
            try:
                fpstags = f.find("streams").find("file")[0].findall("fps")
            except:
                log_traceback()
                fps = self.default_fps

            else:
                if len(fpstags) == 2:
                    fps = int(fpstags[0].text) / int(fpstags[1].text)
                elif len(fpstags) == 1:
                    fps = float(fpstags[0].text)
            data["fps"] = fps

            # position and duration
            times = f.findall("time")
            if len(times) == 2:
                data["pos"] = int(float(times[0].text) * fps)
                data["dur"] = int(float(times[1].text) * fps)
        else:
            data["current"] = LIVE
        return data




def get_info_parser(caspar):
    res = caspar.query("version")
    if res.is_error:
        logging.error("Unable to get casparcg version")
        return False

    parsers = {
            "2.2.0" : Caspar22InfoParser,
            "2.1"   : Caspar21InfoParser,
            "2.0.7" : Caspar207InfoParser,
            "2.0.6" : Caspar207InfoParser, # Same xml as 2.0.7
        }

    Parser = None
    for parser_name in parsers:
        if res.data.startswith(parser_name):
            logging.info("Using CasparCG {} info parser".format(parser_name))
            Parser = parsers[parser_name]
            break

    if not Parser:
        logging.error("Unsupported CasparCG version {}".format(res.data))
    return Parser
