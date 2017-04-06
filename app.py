# -*- coding: utf-8 -*-

import tank
from tank import TankError

class MultiDependencies(tank.platform.Application):

    def init_app(self):

        """
        Called as the application is being initialized
        """
        
        tk_multi_depedencies = self.import_module("tk_multi_depedencies")
        
        # register commands:
        display_name = self.get_setting("display_name")
        
        # "Publish Render" ---> publish_render
        command_name = display_name.lower().replace(" ", "_")
        if command_name.endswith("..."):
            command_name = command_name[:-3]
        params = {"short_name": command_name, 
                  "title": "%s..." % display_name,
                  "description": "Publishing dependencies into Shotgun"}

        show_dialog_callback = lambda: self.engine.show_dialog(display_name, self, tk_multi_depedencies.Dialog, self)
        
        self.log_debug("Registering command for tk-multi-dependencies")
        self.engine.register_command("%s..." % display_name, 
                                     show_dialog_callback, 
                                     params)

