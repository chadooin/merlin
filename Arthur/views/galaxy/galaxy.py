# This file is part of Merlin/Arthur.
# Merlin/Arthur is the Copyright (C)2009,2010 of Elliot Rosemarine.

# Individual portions may be copyright by individual contributors, and
# are included in this collective work with permission of the copyright
# owners.

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
 
from datetime import timedelta
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased
from sqlalchemy.sql import asc, desc
from Core.paconf import PA
from Core.db import session
from Core.maps import Updates, Galaxy, GalaxyHistory, Planet, PlanetExiles, Alliance, Intel
from Arthur.context import render
from Arthur.loadable import loadable, load

@load
class galaxy(loadable):
    def execute(self, request, user, x, y, h=False, ticks=None):
        galaxy = Galaxy.load(x,y)
        if galaxy is None:
            return HttpResponseRedirect(reverse("galaxy_ranks"))
        
        ticks = int(ticks or 0) if h else 12
        
        Q = session.query(Planet, Intel.nick, Alliance.name)
        Q = Q.outerjoin(Planet.intel)
        Q = Q.outerjoin(Intel.alliance)
        Q = Q.filter(Planet.active == True)
        Q = Q.filter(Planet.galaxy == galaxy)
        Q = Q.order_by(asc(Planet.z))
        planets = Q.all() if not h else None
        
        Q = session.query(PlanetExiles)
        Q = Q.filter(or_(PlanetExiles.old == galaxy, PlanetExiles.new == galaxy))
        Q = Q.order_by(desc(PlanetExiles.tick))
        exiles = Q[:10] if not h else None
        
        history = aliased(GalaxyHistory)
        next = aliased(GalaxyHistory)
        membersdiff = history.members - next.members
        sizediff = history.size - next.size
        sizediffvalue = sizediff * PA.getint("numbers", "roid_value")
        valuediff = history.value - next.value
        valuediffwsizevalue = valuediff - sizediffvalue
        resvalue = valuediffwsizevalue * PA.getint("numbers", "res_value")
        shipvalue = valuediffwsizevalue * PA.getint("numbers", "ship_value")
        xpdiff = history.xp - next.xp
        xpvalue = xpdiff * PA.getint("numbers", "xp_value")
        scorediff = history.score - next.score
        realscorediff = history.real_score - next.real_score
        Q = session.query(history, Updates.timestamp - timedelta(minutes=1),
                            next.score_rank, membersdiff,
                            sizediff, sizediffvalue,
                            valuediff, valuediffwsizevalue,
                            resvalue, shipvalue,
                            xpdiff, xpvalue,
                            scorediff, realscorediff
                            )
        Q = Q.join(Updates)
        Q = Q.outerjoin((next, and_(history.id==next.id, history.tick-1==next.tick)))
        Q = Q.filter(history.current == galaxy)
        Q = Q.order_by(desc(history.tick))
        
        return render(["galaxy.tpl","hgalaxy.tpl"][h],
                        request,
                        galaxy = galaxy,
                        planets = planets,
                        exilecount = len(galaxy.outs),
                        exiles = exiles,
                        history = Q[:ticks] if ticks else Q.all(),
                        ticks = ticks,
                      )
