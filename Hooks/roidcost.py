# This file is part of Merlin.
 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 
# This work is Copyright (C)2008 of Robin K. Hansen, Elliot Rosemarine.
# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

import re
from .Core.modules import M
loadable = M.loadable.loadable
from Hooks.ships import feud

class roidcost(loadable):
    """Calculate how long it will take to repay a value loss capping roids."""
    
    def __init__(self):
        loadable.__init__(self)
        self.paramre = re.compile(r"\s+(\d+)\s+(\d+(?:\.\d+)?[km]?)(?:\s+(\d+))?")
        self.usage += " <roids> <value_cost> [mining_bonus]"
    
    @loadable.run
    def execute(self, message, user, params):
        
        roids, cost, bonus = params.groups()
        roids, cost, bonus = int(roids), self.short2num(cost), int(bonus or 0)
        mining = 250

        if roids == 0:
            message.reply("Another NewDawn landing, eh?")
            return

        mining=mining * ((float(bonus)+100)/100)

        repay=int((cost*100)/(roids*mining))

        reply="Capping %s roids at %s value with %s%% bonus will repay in %s ticks (%s days)" % (roids,self.num2short(cost),bonus,repay,repay/24)

        repay = int((cost*100)/(roids*mining*(1/(1-float(feud)))))
        reply+=" Feudalism: %s ticks (%s days)" % (repay,repay/24)

        message.reply(reply)