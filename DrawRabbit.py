"""
Draws a simple cartoon rabbit using turtle graphics.
Run with: python draw_rabbit.py
"""

import turtle


def setup():
    screen = turtle.Screen()
    screen.bgcolor("white")
    screen.title("Turtle Rabbit")

    t = turtle.Turtle()
    t.speed(6)
    t.hideturtle()
    return screen, t


def draw_circle(t, x, y, radius, color="white", outline="black"):
    t.penup()
    t.goto(x, y - radius)
    t.setheading(0)
    t.pendown()
    t.color(outline, color)
    t.begin_fill()
    t.circle(radius)
    t.end_fill()


def draw_ear(t, x, y, angle):
    t.penup()
    t.goto(x, y)
    t.setheading(angle)
    t.pendown()
    t.color("black", "white")
    t.begin_fill()
    t.forward(90)
    t.right(150)
    t.forward(45)
    t.right(60)
    t.forward(45)
    t.right(150)
    t.forward(90)
    t.end_fill()


def draw_face_details(t, cx, cy):
    # Eyes
    draw_circle(t, cx - 20, cy + 15, 5, "black", "black")
    draw_circle(t, cx + 20, cy + 15, 5, "black", "black")

    # Nose
    draw_circle(t, cx, cy, 6, "pink", "black")

    # Mouth
    t.penup()
    t.goto(cx, cy - 6)
    t.setheading(250)
    t.pendown()
    t.color("black")
    t.circle(10, 80)

    t.penup()
    t.goto(cx, cy - 6)
    t.setheading(290)
    t.pendown()
    t.circle(-10, 80)

    # Whiskers
    for dx, angle in [(-15, 200), (-15, 180), (-15, 160),
                       (15, -20), (15, 0), (15, 20)]:
        t.penup()
        t.goto(cx + dx, cy - 2)
        t.setheading(angle)
        t.pendown()
        t.forward(35)


def draw_rabbit():
    screen, t = setup()

    body_x, body_y = 0, -120
    head_x, head_y = 0, 30

    # Ears (drawn first, behind head)
    draw_ear(t, -30, head_y + 30, 100)
    draw_ear(t, 30, head_y + 30, 80)

    # Body
    draw_circle(t, body_x, body_y, 90)

    # Head
    draw_circle(t, head_x, head_y, 60)

    # Face details
    draw_face_details(t, head_x, head_y)

    # Feet
    draw_circle(t, -40, body_y - 80, 22)
    draw_circle(t, 40, body_y - 80, 22)

    # Tail
    draw_circle(t, 85, body_y - 20, 18)

    turtle.done()


if __name__ == "__main__":
    draw_rabbit()
