"""
War Room Core
Sala de crise e comando operacional global
"""

class WarRoom:
    def __init__(self):
        self.incidents = []
        self.sessions = []
        self.commands = []

    def log_incident(self, incident):
        self.incidents.append(incident)

    def start_session(self, session):
        self.sessions.append(session)

    def issue_command(self, command):
        self.commands.append(command)

    def get_status(self):
        return {
            "incidents": self.incidents,
            "sessions": self.sessions,
            "commands": self.commands
        }
