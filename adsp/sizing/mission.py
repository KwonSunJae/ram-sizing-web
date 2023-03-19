import adsp.paths
import csv

class MissionSegment(object):
    def __init__(self, name):
        self.name = str(name)
        self.start_altitude = 0
        self.end_altitude   = 0
        self.speed          = 0
        self.duration       = 0
        self.range          = 0


class MissionProfile(object):
    def __init__(self) -> None:
        self.name = ''
        self.seg = list()
        self.init_altitude = 0
        self.init_speed = 0

    def read_csv(self, filename):
        path = adsp.paths.db.get_sizing_mission_path(filename)
        with open(path, mode='r', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            next(reader)

            row = next(reader)
            self.init_altitude = float(row[1])
            self.init_speed = float(row[3])
            init_seg = MissionSegment(row[0])
            init_seg.start_altitude = float(row[1])
            init_seg.speed = float(row[3])
            self.seg.append(init_seg)

            for row in reader:
                self.add_segment(row)
            self.seg = self.seg[1::]

    def add_segment(self, row):
        new_seg = MissionSegment(row[0])
        if row[1]=='':
            new_seg.start_altitude = self.seg[-1].end_altitude
        else:
            new_seg.start_altitude = float(row[1])
        
        if row[2]=='':
            new_seg.end_altitude = new_seg.start_altitude
        else:
            new_seg.end_altitude = float(row[2])
        
        if row[3]=='':
            new_seg.speed = 0
        else:
            new_seg.speed = float(row[3])

        if row[4]=='':
            new_seg.range = 0
        else:
            new_seg.range = float(row[4])
        
        if row[5]=='':
            new_seg.duration = 0
        else:
            new_seg.duration = float(row[5])
        
        self.seg.append(new_seg)

    def __repr__(self):
        out = f'mission: {self.name}\n'
        out += '{0:<12} {1:^8} {2:^8} {3:^8} {4:^8} {5:^8}\n'.format(
            'SEGMENT', 'START-ALT', 'END-ALT', 'SPEED', 'RANGE', 
            'DURATION')
        out += '-'*len(out) + '\n'
        for seg in self.seg:
            out += '{0:<12} {1:<8.2f} {2:<8.2f} {3:<8.2f} {4:<8.0f} {5:<8.0f}\n'.format(
                seg.name, seg.start_altitude, seg.end_altitude, 
                seg.speed, seg.range, seg.duration)
        return out
        

