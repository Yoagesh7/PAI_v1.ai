
# 14-Day Zero-to-Hero Flow
# This file defines the daily missions for new users.

FLOW_PLAN = {
    1: [
        "💧 Drink a glass of water immediately upon waking up",
        "🛏️ Make your bed to start with a win",
        "📱 No social media for the first 30 mins of the day"
    ],
    2: [
        "🚶 Go for a 10-minute walk outside",
        "🍎 Eat one piece of fruit",
        "📝 Write down 3 things you are grateful for"
    ],
    3: [
        "📖 Read 5 pages of a book",
        "🧹 Clean your workspace for 5 minutes",
        "💧 Drink 2 liters of water today"
    ],
    4: [
        "🧘 Meditate for 5 minutes (Focus on breath)",
        "📵 Put your phone in another room for 1 hour",
        "🥗 Eat a healthy meal with no processed food"
    ],
    5: [
        "🏋️ Do 20 pushups or squats",
        "🧊 Take a cold ends shower (30 seconds)",
        "📅 Plan tomorrow's top 3 tasks tonight"
    ],
    6: [
        "🚫 No sugar today",
        "📞 Call a friend or family member just to say hi",
        "🚶 20-minute walk without phone/music"
    ],
    7: [
        "🌲 Spend 30 minutes in nature",
        "🧘 10-minute meditation",
        "📝 Review your week: What went well?"
    ],
    # Week 2: Ramping Up
    8: [
        "⏰ Wake up 30 minutes earlier than usual",
        "📖 Read 10 pages",
        "🏋️ 30-minute workout"
    ],
    9: [
        "📵 Digital Detox: No screens after 8 PM",
        "💧 3 liters of water",
        "🧠 Learn something new for 15 minutes (video/article)"
    ],
    10: [
        "🥗 Intermittent Fasting: 12-hour window",
        "🧹 Deep clean one area of your room/house",
        "📝 Journal: Who do I want to be in 1 year?"
    ],
    11: [
        "🚫 No complaints today (Mental Diet)",
        "🏋️ High-Intensity Interval Training (15 mins)",
        "🧊 1-minute cold shower"
    ],
    12: [
        "🧘 15-minute meditation",
        "📵 No social media all day (Challenge)",
        "🍎 Eat only whole foods today"
    ],
    13: [
        "🕯️ Candlelight evening: No electric lights after sunset",
        "📖 Read 20 pages",
        "📝 Write a letter to your future self"
    ],
    14: [
        "⛰️ The Big Challenge: 1-hour workout or long hike",
        "🧘 20-minute meditation",
        "🎉 Celebrate: You completed the 14-Day Flow!"
    ]
}

def get_day_content(day):
    return FLOW_PLAN.get(day, [])
