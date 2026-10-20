from scripts.build_pages import keep_history, HISTORY_LIMIT

def test_history_only_real_observations():
    record={"status":"LIVE","observed_at":"2026-10-20 11:40","population_min":1000,"population_max":2000,"congestion":"보통"}
    h=keep_history([],record)
    assert len(h)==1
    assert keep_history(h,record)==h
    assert keep_history(h,{"status":"API_ERROR","observed_at":None})==h

def test_history_retention():
    previous=[{"observed_at":f"2026-10-{n:02d} 10:00","population_min":n,"population_max":n+1} for n in range(1,70)]
    assert len(keep_history(previous,{"status":"UNAVAILABLE"}))==HISTORY_LIMIT
