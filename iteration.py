import itertools
import random


# 1. Basic for-loop over a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(f"Fruit: {fruit}")

# 2. enumerate() gives the index and value
for i, fruit in enumerate(fruits, start=1):
    print(f"{i}. {fruit}")

# 3. zip() iterates over several sequences in parallel
scores = [random.randint(50, 100) for _ in fruits]
for fruit, score in zip(fruits, scores):
    print(f"{fruit} scored {score}")

# 4. Dictionary iteration
inventory = {fruit: random.randint(1, 20) for fruit in fruits}
for name, qty in inventory.items():
    print(f"{name}: {qty} in stock")


# 5. A custom iterator class
class Countdown:
    def __init__(self, start):
        self.current = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


print("Countdown:", list(Countdown(5)))


# 6. A generator function (lazy iteration)
def random_walk(steps):
    position = 0
    for _ in range(steps):
        position += random.choice([-1, 1])
        yield position


print("Random walk:", list(random_walk(10)))

# 7. Comprehensions and generator expressions
squares = [n**2 for n in range(1, 8)]
even_squares = (n for n in squares if n % 2 == 0)  # lazy
print("Squares:", squares)
print("Even squares:", list(even_squares))

# 8. itertools: combinations and an infinite cycle, sliced
print("Pairs:", list(itertools.combinations(fruits, 2)))
colors = itertools.cycle(["red", "green", "blue"])
print("Cycle:", [next(colors) for _ in range(7)])

# 9. while loop with a random stopping condition
attempts = 0
roll = 0
while roll != 6:
    roll = random.randint(1, 6)
    attempts += 1
print(f"Rolled a 6 after {attempts} attempt(s)")

# 10. for/else: the else runs only if the loop wasn't broken
for n in range(2, 10):
    if n == random.randint(2, 20):
        print(f"Found {n}")
        break
else:
    print("No match found")
