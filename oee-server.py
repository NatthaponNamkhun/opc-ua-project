from opcua import Server
from random import randint, uniform
import datetime
import time

server = Server()
url = "opc.tcp://localhost:4840"
server.set_endpoint(url)

name     = "OEE-Server"
addspace = server.register_namespace(name)
node     = server.get_objects_node()
Param    = node.add_object(addspace, "MachineOEE")

ProducedParts = Param.add_variable(addspace, "ProducedParts", 850) # ชิ้นงานที่ผลิตได้ (สะสม2)
# Availability
PlannedTime     = Param.add_variable(addspace, "PlannedTime",     480)   # 8 hr.
Downtime        = Param.add_variable(addspace, "Downtime",        0.0)
Availability    = Param.add_variable(addspace, "Availability",    100.0)  # 100%
Runtime         = Param.add_variable(addspace, "Runtime",         0)

# Performance
IdealCycleTime  = Param.add_variable(addspace, "IdealCycleTime",  10.0)  # 10 วินาทีต่อชิ้น
ActualCycleTime = Param.add_variable(addspace, "ActualCycleTime", 10.0) # 10.2 วินาทีต่อชิ้น
Performance     = Param.add_variable(addspace, "Performance",     100.0)

# Quality
TotalParts      = Param.add_variable(addspace, "TotalParts",      0)
GoodParts       = Param.add_variable(addspace, "GoodParts",       0)
Quality         = Param.add_variable(addspace, "Quality",         100.0)
Reject          = Param.add_variable(addspace, "Reject",          0)


# OEE
OEE             = Param.add_variable(addspace, "OEE",             100.0)

# Time
Duration = Param.add_variable(addspace, "Duration",     0)  
Datetime = Param.add_variable(addspace, "Datetime",     "")    
Time = Param.add_variable(addspace, "Time",     "") 

# Set Writable
for var in [PlannedTime, Downtime, Availability, Runtime,ProducedParts,
            IdealCycleTime, ActualCycleTime, Performance,
            TotalParts, GoodParts, Quality, OEE, Duration, Datetime, Time, Reject]:
    var.set_writable()

server.start()
print("OEE Server started at {}".format(url))

# Start Simulation of OEE data
produced_parts = 850   
planned     = 480      
runtime     = 0.0       
downtime    = 0.0       
total_parts = 0         
good_parts  = 0         
reject      = 0         
start_time  = time.time() 

while True:
    elapsed = (time.time() - start_time) / 60

    # Downtime
    if uniform(0, 100) <= 7:
        downtime += 0.15

    runtime = max(0.0, elapsed - downtime)

    # Fab sim
    actual_ct    = uniform(9.9, 12.5)
    total_parts += 1

    # 97% > good, 3% > reject
    if uniform(0, 100) <= 95:
        good_parts += 1
    else:
        reject += 1

    # OEE Cal
    runtime_sec = runtime * 60  

    avail = round((runtime / elapsed) * 100, 2) if elapsed > 0 else 100.0
    avail = max(0.0, min(100.0, avail))

    perf = round((IdealCycleTime.get_value() * total_parts) / runtime_sec * 100, 2) if runtime_sec > 0 else 0.0
    perf = max(0.0, min(100.0, perf))

    qual = round(good_parts / total_parts * 100, 2) if total_parts > 0 else 100.0

    oee  = round((avail / 100) * (perf / 100) * (qual / 100) * 100, 2)

    duration = round(elapsed, 2)
    date     = datetime.datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.datetime.now().strftime("%H:%M:%S")

    # Update OPC-UA
    PlannedTime.set_value(planned)
    Downtime.set_value(downtime)
    Runtime.set_value(runtime)
    Availability.set_value(avail)
    ActualCycleTime.set_value(actual_ct)
    Performance.set_value(perf)
    TotalParts.set_value(total_parts)
    GoodParts.set_value(good_parts)
    Quality.set_value(qual)
    OEE.set_value(oee)
    Duration.set_value(duration)
    Datetime.set_value(date)
    Time.set_value(time_str)
    Reject.set_value(reject)
    ProducedParts.set_value(produced_parts)

    # Reset ทุก 8 ชั่วโมง
    if elapsed >= 480:
        print("Reset....")
        downtime    = 0.0
        total_parts = 0
        good_parts  = 0
        reject      = 0
        start_time  = time.time()

    print(f"Elapsed: {elapsed:.1f} min | "
          f"OEE: {oee}% | "
          f"A: {avail}% | "
          f"P: {perf}% | "
          f"Q: {qual}% | "
          f"Total: {total_parts} | "
          f"Good: {good_parts} | "
          f"Reject: {reject} | "
          f"Downtime: {downtime:.1f} min")

    time.sleep(5) # ส่งค่าทุก ๆ 5 วินาที