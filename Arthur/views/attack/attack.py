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
 
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from sqlalchemy.sql import asc
from Core.db import session
from Core.maps import Updates, Planet, Target, Attack
from Core.config import Config
from Arthur.context import menu, render
from Arthur.loadable import loadable, load

@menu("Attacks")
@load
class attack(loadable):
    access = "half"
    
    def execute(self, request, user, message=None):
        tick = Updates.current_tick()
        
        Q = session.query(Attack)
        if user.access < (Config.getint("Access",  "hc") if "hc" in Config.options("Access") else 1000): # Hide attacks until they are active, unless the user has access
            Q = Q.filter(Attack.landtick <= tick + Config.getint("Misc", "attactive"))
        Q = Q.filter(Attack.landtick + Attack.waves >= tick) # Hide attacks one tick after the last wave has landed
        Q = Q.order_by(asc(Attack.id))
        attacks = Q.all()
        
        Q = session.query(Planet, Target.tick)
        Q = Q.join(Target.planet)
        Q = Q.join(Target.user)
        Q = Q.filter(Planet.active == True)
        Q = Q.filter(Target.user == user)
        Q = Q.filter(Target.tick >= tick - 12) # We shouldn't need any bookings 12 ticks after landing
        Q = Q.order_by(asc(Target.tick), asc(Planet.x), asc(Planet.y), asc(Planet.z))
        
        bookings = []
        scans = []
        for planet, tock in Q.all():
            bookings.append((planet, tock, [],))
            if planet.scan("P"):
                bookings[-1][2].append(planet.scan("P"))
                scans.append(planet.scan("P"))
            
            if planet.scan("D"):
                bookings[-1][2].append(planet.scan("D"))
                scans.append(planet.scan("D"))
            
            if planet.scan("A") or planet.scan("U"):
                bookings[-1][2].append(planet.scan("A") or planet.scan("U"))
                scans.append(planet.scan("A") or planet.scan("U"))
            
            if tock <= tick + Config.getint("Misc", "attjgp") and planet.scan("J"):
                bookings[-1][2].append(planet.scan("J"))
                scans.append(planet.scan("J"))
        
        return render("attacks.tpl", request, message=message, attacks=attacks, bookings=bookings, scans=scans)

@load
class view(loadable):
    access = "half"
    
    def execute(self, request, user, id, message=None):
        attack = Attack.load(id)
        if attack is None or not attack.active:
            return HttpResponseRedirect(reverse("attacks"))
        
        waves = xrange(attack.landtick, attack.landtick + attack.waves)
        show_jgps = attack.landtick <= Updates.current_tick() + Config.getint("Misc", "attjgp")
        
        group = []
        scans = []
        for planet in attack.planets:
            group.append((planet, [], [],))
            if planet.scan("P"):
                group[-1][1].append(planet.scan("P"))
                scans.append(planet.scan("P"))
            
            if planet.scan("D"):
                group[-1][1].append(planet.scan("D"))
                scans.append(planet.scan("D"))
            
            if planet.scan("A"):
                if planet.scan("U"):
                    if planet.scan("U").tick > planet.scan("A").tick + 12:
                        group[-1][1].append(planet.scan("U"))
                        scans.append(planet.scan("U"))
                    elif planet.scan("U").tick > planet.scan("A").tick:
                        group[-1][1].append(planet.scan("U"))
                        scans.append(planet.scan("U"))
                        group[-1][1].append(planet.scan("A"))
                        scans.append(planet.scan("A"))
                    else:
                        group[-1][1].append(planet.scan("A"))
                        scans.append(planet.scan("A"))
                else:
                    group[-1][1].append(planet.scan("A"))
                    scans.append(planet.scan("A"))
            elif planet.scan("U"):
                group[-1][1].append(planet.scan("U"))
                scans.append(planet.scan("U"))
            
            if show_jgps and planet.scan("J"):
                group[-1][1].append(planet.scan("J"))
                scans.append(planet.scan("J"))
            
            bookings = dict([(target.tick, target,) for target in planet.bookings.filter(Target.tick.between(attack.landtick, attack.landtick+attack.waves+1))])
            for tick in waves:
                group[-1][2].append((tick, bookings.get(tick) or (False if show_jgps else None),))
        
        return render("attack.tpl", request, attack=attack, message=message, waves=waves, group=group, scans=scans)
