def daily_report(name, tasks, career):
    done = len([t for t in tasks if t[1] == "done"])
    total = len(tasks)

    return f"""
 Daily Report  {name}

 Goal: {career}
 Tasks completed: {done}/{total}
 Consistency: {"Strong" if done == total else "Improving"}
 Insight: Small steps done well
 Tomorrow: Continue momentum
"""
