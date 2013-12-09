#
# core.py
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
# 	The Free Software Foundation, Inc.,
# 	51 Franklin Street, Fifth Floor
# 	Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

from deluge.log import LOG as log
from deluge.plugins.pluginbase import CorePluginBase
import deluge.component as component
import re
import urllib2
from threading import Thread

def log_debug(message):
    log.debug('Torrentz plugin: %s' % message)

class TrackersAdder(Thread):
    def __init__(self,torrent_id):
        Thread.__init__(self)
        self.torrent_id = torrent_id
    
    def get_torrentz_trackers(self,torrent_id):
        torrentz_url = 'https://torrentz.eu'
        html = urllib2.urlopen('%s/%s' % (torrentz_url,torrent_id) ).read()
        announce = re.search('/announcelist_[a-z0-9]+',html).group(0)
        new_trackers = urllib2.urlopen('%s%s' % (torrentz_url,announce) ).read()
        return [x.strip() for x in new_trackers.splitlines() if x.strip() != '']

    def run(self):
        torrent = component.get("TorrentManager")[self.torrent_id]
        trackers = torrent.get_status(["trackers"])["trackers"]
        existing_urls = [tracker["url"] for tracker in trackers]
        
        new_trackers = self.get_torrentz_trackers(self.torrent_id)

        got_new_trackers = False
        for new_tracker in new_trackers:
            if new_tracker not in existing_urls:
                got_new_trackers = True
                trackers.append({ "tier": len(trackers), "url": new_tracker, })

        if got_new_trackers:
            n = len(trackers) - len(existing_urls)
            log_debug('%d new trackers added' % n )
            torrent.set_trackers(trackers)


class Core(CorePluginBase):

    def enable(self):
        log_debug('enabled')
        component.get("EventManager").register_event_handler("TorrentAddedEvent", self.on_torrent_added)

    def disable(self):
        log_debug('disabled')
        component.get("EventManager").deregister_event_handler("TorrentAddedEvent", self.on_torrent_added)

    def update(self):
        pass
        
    def on_torrent_added(self, torrent_id):
        log_debug('Torrent added detected --> %s' % torrent_id )
        TrackersAdder(torrent_id).start()

