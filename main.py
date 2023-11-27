import os
import subprocess
import json
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction


def scan_edge_folder(edge_config_folder):
    profiles = {}
    # First, let's extract profiles from Local State JSON
    with open(os.path.join(edge_config_folder, 'Local State')) as f:
        local_state = json.load(f)
        cache = local_state['profile']['info_cache']
        for folder, profile_data in cache.items():
            profiles[folder] = {
                'name': profile_data['name'],
                'email': profile_data['user_name']
            }

    # Leave out every past profile which doesn't exist anymore
    for folder in list(profiles.keys()):
        try:
            os.listdir(os.path.join(edge_config_folder, folder))
        except FileNotFoundError:
            profiles.pop(folder)

    return profiles


class EdgeExtension(Extension):
    def __init__(self):
        super(EdgeExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, EdgeKeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, EdgeItemEnterEventListener())


class EdgeKeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        edge_config_folder = os.path.expanduser(extension.preferences['edge_folder'])
        profiles = scan_edge_folder(edge_config_folder)

        # Filter by query if inserted
        query = event.get_argument()
        if query:
            query = query.strip().lower()
            for folder in list(profiles.keys()):
                name = profiles[folder]['name'].lower()
                if query not in name:
                    profiles.pop(folder)

        # Create launcher entries
        entries = []
        for folder in profiles:
            entries.append(ExtensionResultItem(
                icon='images/icon.png',  # Change this to the Edge icon
                name=profiles[folder]['name'],
                description=profiles[folder]['email'],
                on_enter=ExtensionCustomAction({
                    'edge_cmd': extension.preferences['edge_cmd'],
                    'opt': ['--profile-directory={0}'.format(folder)]
                }, keep_app_open=True)
            ))
        return RenderResultListAction(entries)


class EdgeItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        # Open Edge when user selects an entry
        data = event.get_data()
        edge_path = data['edge_cmd']
        opt = data['opt']
        subprocess.Popen([edge_path] + opt)


if __name__ == '__main__':
    EdgeExtension().run()
