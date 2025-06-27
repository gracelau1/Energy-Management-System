from datetime import datetime, timedelta, date
import csv

class SmartLightingController:
    def __init__(self, room_config):
        self.room_config = room_config
        self.room_states = {room: {'light_on': False, 'manual_override': False} for room in room_config}
        self.room_counters = {room: 0 for room in room_config}  # Track occupancy count per room
        self.energy_log = []
        self.total_energy_used = 0.0
        self.total_energy_no_ems = 0.0
        self.total_energy_saved = 0.0
        self.room_energy_used = {room: 0.0 for room in room_config}
        self.room_energy_no_ems = {room: 0.0 for room in room_config}
        self.last_energy_calc_time = None
        self.simulation_time = datetime.combine(date.today(), datetime.strptime('08:00', '%H:%M').time())
        self.csv_event_queue = []

    def advance_simulation_time(self, seconds=10):
        next_time = (self.simulation_time + timedelta(seconds=seconds)).replace(microsecond=0)
        if next_time.second % 10 != 0:
            next_time += timedelta(seconds=(10 - next_time.second % 10))
        self.simulation_time = next_time
        self._process_queued_csv_events()
        self._update_all_room_status(now=self.simulation_time)

    def _update_all_room_status(self, now):
        hour = now.hour
        working_hours = 8 <= hour < 21
        for room, config in self.room_config.items():
            state = self.room_states[room]
            occupancy = self.room_counters[room]

            if state['manual_override']:
                state['light_on'] = True
            else:
                if config['essential']:
                    if working_hours:
                        state['light_on'] = True
                    else:
                        state['light_on'] = (occupancy >= 1)
                else:
                    state['light_on'] = (occupancy >= 1)
        self._update_energy_usage(now)

    def _update_energy_usage(self, now):
        if self.last_energy_calc_time is None:
            self.last_energy_calc_time = now
            return
        elapsed = (now - self.last_energy_calc_time).total_seconds() / 3600.0
        
        #calculate energy increase for (with EMS)
        for room, config in self.room_config.items():
            if self.room_states[room]['light_on']:
                self.room_energy_used[room] += (config['light_power_watts'] / 1000.0) * elapsed
        
        #calculate energy increase for (without EMS)
        for room, config in self.room_config.items():
            occupied = (self.room_counters[room] > 0)
            if 8 <= now.hour < 21:
                #for without EMS, all rooms ON during working hours
                self.room_energy_no_ems[room] += (config['light_power_watts'] / 1000.0) * elapsed
            else:
                #for without EMS, after working hours, lights ON if occupied
                if occupied or self.room_states[room]['manual_override']:
                    self.room_energy_no_ems[room] += (config['light_power_watts'] / 1000.0) * elapsed

        self.total_energy_used = sum(self.room_energy_used.values())
        self.total_energy_no_ems = sum(self.room_energy_no_ems.values())
        self.total_energy_saved = self.total_energy_no_ems - self.total_energy_used
        self.last_energy_calc_time = now


    #returns total energy stats
    def get_energy_totals(self):
        return {
            'used': round(self.total_energy_used, 3),
            'no_ems': round(self.total_energy_no_ems, 3),
            'saved': round(self.total_energy_saved, 3)
        }

    #returns per-room energy stats
    def get_energy_per_room(self):
        return {room: round(v, 3) for room, v in self.room_energy_used.items()}

    def get_energy_per_room_no_ems(self):
        return {room: round(v, 3) for room, v in self.room_energy_no_ems.items()}

    def get_energy_per_room_saved(self):
        return {room: round(self.room_energy_no_ems[room] - self.room_energy_used[room], 3) for room in self.room_config}

    #returns current room state
    def get_states(self):
        return self.room_states

    #returns current energy log
    def get_log(self):
        return self.energy_log

    #lets frontend force a room’s light state manually
    def update_room(self, room, light_on, manual_override=False):
        self.room_states[room].update({
            'light_on': light_on,
            'manual_override': manual_override
        })
    
    def fast_forward_to_8am_next_day(self):
        next_day_8am = (self.simulation_time + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        while self.simulation_time < next_day_8am:
            self.advance_simulation_time(10)  # Fast forward in 10-second steps


    def process_csv(self, csv_path):
        try:
            with open(csv_path, 'r') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) != 3:
                        continue
                    time_str, room, action = map(str.strip, row)
                    try:
                        event_time = datetime.combine(self.simulation_time.date(), datetime.strptime(time_str, "%H:%M").time())
                    except ValueError:
                        continue
                    if room in self.room_config:
                        detected = action.lower() == 'enter'
                        self.csv_event_queue.append((event_time, room, detected))
                self.csv_event_queue.sort(key=lambda x: x[0])
        except Exception as e:
            print(f"CSV processing error: {e}")

    def _process_queued_csv_events(self):
        processed = []
        for event_time, room, detected in self.csv_event_queue:
            if event_time <= self.simulation_time:
                timestamp = event_time.strftime('%H:%M')
                if detected:
                    self.room_counters[room] += 1
                    self.energy_log.append(f"[{timestamp}] Employee entered {room}. Occupancy: {self.room_counters[room]}")
                else:
                    self.room_counters[room] = max(0, self.room_counters[room] - 1)
                    self.energy_log.append(f"[{timestamp}] Employee left {room}. Occupancy: {self.room_counters[room]}")
                processed.append((event_time, room, detected))
        for event in processed:
            self.csv_event_queue.remove(event)


# Default room_config (can be replaced via upload)
room_config = {
    "Open Workspace": {"essential": False, "light_power_watts": 20, "delay_off_seconds": 5},
    "Meeting Room": {"essential": False, "light_power_watts": 18, "delay_off_seconds": 5},
    "Pantry": {"essential": False, "light_power_watts": 15, "delay_off_seconds": 0},
    "Server Room": {"essential": True, "light_power_watts": 25, "delay_off_seconds": 0},
    "Rest Area": {"essential": False, "light_power_watts": 10, "delay_off_seconds": 2},
    "Design Lab": {"essential": True, "light_power_watts": 28, "delay_off_seconds": 0},
    "Offices": {"essential": False, "light_power_watts": 12, "delay_off_seconds": 0}
}

