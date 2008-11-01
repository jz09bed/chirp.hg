#!/usr/bin/python
#
# Copyright 2008 Dan Smith <dsmith@danplanet.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import errors

from chirp import chirp_common

def get_memory(doc, number):
    ctx = doc.xpathNewContext()

    base = "//radio/memory[@location=%i]" % number

    fields = ctx.xpathEval(base)
    if len(fields) > 1:
        raise errors.RadioError("%i memories claiming to be %i" % (len(fields),
                                                                   number))
    elif len(fields) == 0:
        raise errors.InvalidMemoryLocation("%i does not exist" % number)

    memnode = fields[0]

    def _get(ext):
        path = base + ext
        return ctx.xpathEval(path)[0].getContent()

    if _get("/mode/text()") == "DV":
        mem = chirp_common.DVMemory()
        mem.dv_urcall = _get("/dv/urcall/text()")
        mem.dv_rpt1call = _get("/dv/rpt1call/text()")
        mem.dv_rpt2call = _get("/dv/rpt2call/text()")
    else:
        mem = chirp_common.Memory()

    mem.number = int(memnode.prop("location"))
    mem.name = _get("/longName/text()")
    mem.freq = float(_get("/frequency/text()"))
    mem.rtone = float(_get("/squelch[@id='rtone']/tone/text()"))
    mem.ctone = float(_get("/squelch[@id='ctone']/tone/text()"))
    mem.dtcs = int(_get("/squelch[@id='dtcs']/code/text()"), 10)
    mem.dtcs_polarity = _get("/squelch[@id='dtcs']/polarity/text()")
    
    try:
        sql = _get("/squelchSetting/text()")
        if sql == "rtone":
            mem.tmode = "Tone"
        elif sql == "ctone":
            mem.tmode = "TSQL"
        elif sql == "dtcs":
            mem.tmode = "DTCS"
        else:
            mem.tmode = ""
    except IndexError:
        mem.tmode = ""

    dmap = {"positive" : "+", "negative" : "-", "none" : ""}
    dupx = _get("/duplex/text()")
    mem.duplex = dmap.get(dupx, "")

    mem.offset = float(_get("/offset/text()"))
    mem.mode = _get("/mode/text()")
    mem.tuning_step = float(_get("/tuningStep/text()"))

    return mem

def set_memory(doc, mem):
    ctx = doc.xpathNewContext()

    base = "//radio/memory[@location=%i]" % mem.number

    fields = ctx.xpathEval(base)
    if len(fields) > 1:
        raise errors.RadioError("%i memories claiming to be %i" % (len(fields),
                                                                   number))
    elif len(fields) == 1:
        fields[0].unlinkNode()

    radio = ctx.xpathEval("//radio")[0]
    memnode = radio.newChild(None, "memory", None)
    memnode.newProp("location", "%i" % mem.number)

    sname = memnode.newChild(None, "shortName", None)
    sname.addContent(mem.name.upper()[:6])

    lname = memnode.newChild(None, "longName", None)
    lname.addContent(mem.name)
    
    freq = memnode.newChild(None, "frequency", None)
    freq.newProp("units", "MHz")
    freq.addContent("%.5f" % mem.freq)
    
    rtone = memnode.newChild(None, "squelch", None)
    rtone.newProp("id", "rtone")
    rtone.newProp("type", "repeater")
    tone = rtone.newChild(None, "tone", None)
    tone.addContent("%.1f" % mem.rtone)

    ctone = memnode.newChild(None, "squelch", None)
    ctone.newProp("id", "ctone")
    ctone.newProp("type", "ctcss")
    tone = ctone.newChild(None, "tone", None)
    tone.addContent("%.1f" % mem.ctone)

    dtcs = memnode.newChild(None, "squelch", None)
    dtcs.newProp("id", "dtcs")
    dtcs.newProp("type", "dtcs")
    code = dtcs.newChild(None, "code", None)
    code.addContent("%03i" % mem.dtcs)
    polr = dtcs.newChild(None, "polarity", None)
    polr.addContent(mem.dtcs_polarity)

    sset = memnode.newChild(None, "squelchSetting", None)
    if mem.tmode == "Tone":
        sset.addContent("rtone")
    elif mem.tmode == "TSQL":
        sset.addContent("ctone")
    elif mem.tmode == "DTCS":
        sset.addContent("dtcs")

    dmap = {"+" : "positive", "-" : "negative", "" : "none"}
    dupx = memnode.newChild(None, "duplex", None)
    dupx.addContent(dmap[mem.duplex])

    oset = memnode.newChild(None, "offset", None)
    oset.newProp("units", "MHz")
    oset.addContent("%.5f" % mem.offset)

    mode = memnode.newChild(None, "mode", None)
    mode.addContent(mem.mode)

    step = memnode.newChild(None, "tuningStep", None)
    step.newProp("units", "MHz")
    step.addContent("%.5f" % mem.tuning_step)
    
    if isinstance(mem, chirp_common.DVMemory):
        dv = memnode.newChild(None, "dv", None)

        ur = dv.newChild(None, "urcall", None)
        ur.addContent(mem.dv_urcall)

        r1 = dv.newChild(None, "rpt1call", None)
        r1.addContent(mem.dv_rpt1call)

        r2 = dv.newChild(None, "rpt2call", None)
        r2.addContent(mem.dv_rpt2call)

def del_memory(doc, number):
    path = "//radio/memory[@location=%i]" % number
    ctx = doc.xpathNewContext()
    fields = ctx.xpathEval(path)

    for field in fields:
        field.unlinkNode()
    
