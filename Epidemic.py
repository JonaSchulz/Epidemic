import numpy as np
import pygame
import matplotlib.pyplot as plt

size = 1700, 900 # size of screen
width = 5   # width of individuals
black = 0, 0, 0
white = 255, 255, 255
red = 255, 0, 0
blue = 0, 0, 255
grey = 100, 100, 100

# population parameters:
n = 2000     # total population size
number_of_populations = 9   # number of different "countries"
square_dist = 20    # 1/2 distance between two population squares
speed_healthy = 2   # number of pixels individuals can move in the x and y direction each iteration
speed_sick = 2
travel_speed = 7
daily_travellers = 20   # number of individuals that will travel from one population to another within each day
day_length = 100    # number of iterations a day lasts (days are used for data plotting and daily travellers)

# virus parameters:
infection_radius = 5    # radius in pixels around each infected individual within a healthy individual has a risk of infection
infection_risk = 0.5   # risk of infection per iteration for a healthy individual within an infected individual's infection radius
recovery_time = 4   # number of days it takes an infected person to recover and become healthy again
incubation_period = 2  # number of days it takes for an infected individual before there is a chance of death
lethality = 0.8  # chance for an infected individual to die from the virus
acquired_immunity = True    # if True: recovered individuals can't get reinfected

# Statistical data to display:
total_number_of_infected_people = True  # if True: data will be plotted when RETURN is pressed during simulation
daily_number_of_infections = True
total_number_of_deaths = True
daily_number_of_deaths = True
number_of_healthy_people = False
number_of_recovered_people = True


# Population class - creates a list of all separate populations the simulation consists of:
# (contains information about each population's location and physical boundaries
class Population:
    def __init__(self, N, dist, screen):
        self.screen = screen    # pygame screen object used for simulation
        if int(np.sqrt(N))**2 >= N: # algorithm to create N squares and pack them into the screen
            dimensions = (int(round(np.sqrt(N))), int(round(np.sqrt(N))))   # x squares in a row, y squares in a column (x always equal to or one greater than y)
        else:
            dimensions = (int(round(np.sqrt(N)))+1, int(round(np.sqrt(N))))
        self.edge = min([size[0]//dimensions[0], size[1]//dimensions[1]])   # side length of each population square (largest possible)
        squares = []    # list that contains all population squares (location of top left corner)
        for i in range(dimensions[0]):  # fill list with squares (x*y squares)
            for j in range(dimensions[1]):
                squares.append((i*self.edge, j*self.edge))
        while len(squares) > N: # delete any squares that are too many (not always x*y squares)
            squares.pop(-1)
        self.squares = []   # list that contains pygame.Rect objects representing the squares from above
        for i in squares:
            self.squares.append(pygame.Rect(i[0]+dist, i[1]+dist, self.edge-2*dist, self.edge-2*dist))  # each Rect ist smaller by square_dist than the original squares in order to have some space between population squares
        for i in self.squares:
            pygame.draw.rect(screen, white, i, 2)   # display squares on screen

    def draw_squares(self): # method that gets called every iteration to redraw the squares on the screen
        for i in self.squares:
            pygame.draw.rect(self.screen, white, i, 2)


# Epidemic class - contains all rules for virus spread and people's behaviour:
class Epidemic:
    # class variables:
    screen = pygame.display.set_mode(size)  # pygame screen object the simulation gets displayed on
    world = [[0 for i in range(-infection_radius, size[1]+infection_radius+1)] for j in range(-infection_radius, size[0]+infection_radius+1)]   #matrix representation of simulated world (each pixel on screen corresponds to one matrix entry)
    populations = Population(number_of_populations, square_dist, screen)    # Population object that contains information about all population squares
    people = []     # list that contains all individuals (healthy, infected, recovered and dead)
    infected_people = []    # list that contains all infected individuals
    healthy_people = []     # list that contains all healthy individuals (including recovered ones)
    dead_people = []    # list that contains all dead individuals
    recovered_people = []   # list that contains all dead individuals
    travelling_people = []  # list that contains all individuals currently travelling
    death_risk = 1 - np.power(1-lethality, 1/((recovery_time-incubation_period)*day_length))    # risk of death for each individual each iteration calculated from lethality

    # statistical data: (lists that are updated each iteration (or each day for n_daily_infections and n_daily_deaths
    n_daily_deaths = [0]
    n_daily_infections = [0]
    n_infected = [1]
    n_dead = [0]
    n_healthy = [n-1]   # all individuals healthy at start
    n_recovered = [0]
    day = 0     # counter that keeps track of number of days that have passed (one day is day_length iterations long)
    iterations = 0  # counter that keeps track of number of iterations of the main game loop

    def __init__(self, type, population):   # type 1 for healthy, 2 for infected
        # instance variables individual for each person:
        self.population = population    # population square the individual is in (changes when travelling)
        self.infected_days = 0     # counter that keeps track of how many consecutive days the individual has been infected (used for recovery and death)
        if type == 1:   # set speed of individual for moving within its population
            self.speed = speed_healthy
        else:
            self.speed = speed_sick
        self.recovery_time = int(recovery_time*day_length)  # recovery time in iterations
        self.incubation_period = int(incubation_period*day_length)   # incubation period in iterations

        self.travelling = False     # keeps track of whether the individual is currently in transit between two population squares
        self.destination = []   # contains location of travel destination when individual is travelling

        if type == 1:   # set infected status: 0 for healthy, 1 for infected, 2 for recovered, 3 for dead
            self.infected = 0
        else:
            self.infected = 1
        occupied = True
        while occupied:     # find an initial position for the individual within its population square that isn't already occupied by another individual
            self.position = [np.random.randint(population.left, population.right-width+1), np.random.randint(population.top, population.bottom-width+1)]    #random position within population square
            if not Epidemic.world[self.position[0]][self.position[1]]:  # position isn't occupied?
                occupied = False    # exit while loop (initial position has been found)
        Epidemic.world[self.position[0]][self.position[1]] = self   # put the individual as an EPidemic object into the world matrix at the initial position
        Epidemic.people.append(self)    # put individual in people list
        if self.infected:   # if infected, put individual in infected_people list
            Epidemic.infected_people.append(self)
        else:   # if healthy, put individual in healthy_people list
            Epidemic.healthy_people.append(self)
        particle_rect = pygame.Rect(self.position[0], self.position[1], width, width)   # create pygame.Rect object for individual that can be displayed on screen
        if self.infected:   # red square for infected individuals
            pygame.draw.rect(Epidemic.screen, red, particle_rect, 0)
        else:   # white square for healthy individuals
            pygame.draw.rect(Epidemic.screen, white, particle_rect, 0)

    # update_position method - moves individual around within its population (not used for travelling):
    def update_position(self):
        if self.infected != 3:  # only living individuals can move around
            occupied = True
            Epidemic.world[self.position[0]][self.position[1]] = 0  # delete current position of individual from world matrix
            while occupied:     # randomly select next location that isn't already occupied by another individual
                x_motion = np.random.randint(-self.speed, self.speed+1)     # random movement in x direction
                y_motion = np.random.randint(-self.speed, self.speed+1)     # random movement in y direction
                new_x = self.position[0] + x_motion     # new x position
                new_y = self.position[1] + y_motion     # new y position
                if self.population.left <= new_x <= self.population.right-width and self.population.top <= new_y <= self.population.bottom-width:   # check whether new position is still within population square
                    if not Epidemic.world[new_x][new_y]:    # only break while loop when new position isn't occupied
                        occupied = False
                        self.position = [new_x, new_y]  # update individual's position
            Epidemic.world[new_x][new_y] = self     # put new position in world matrix

        # draw person:
        particle_rect = pygame.Rect(self.position[0], self.position[1], width, width)   # create pygame.Rect object for individual that can be displayed on screen
        if self.infected == 1:
            pygame.draw.rect(Epidemic.screen, red, particle_rect, 0)    # red for infected
        elif self.infected == 2:
            pygame.draw.rect(Epidemic.screen, blue, particle_rect, 0)   # blue for recovered and immune
        elif self.infected == 3:
            pygame.draw.rect(Epidemic.screen, grey, particle_rect, 0)   # grey for dead
        else:
            pygame.draw.rect(Epidemic.screen, white, particle_rect, 0)  # white for healthy and not immune

    # update_infection method - used on infected individuals for infection of others within the infection radius, recovery and death:
    def update_infection(self):
        self.infected_days += 1     # increment counter of infected people
        if not self.travelling:     # only infect others while not travelling
            for i in range(-infection_radius, infection_radius + 1):    # check all pixels within infection radius (square-shaped)
                for j in range(-infection_radius, infection_radius + 1):
                    if i == 0 and j == 0:   # skip own position
                        continue
                    if Epidemic.world[self.position[0] + i][self.position[1] + j]:  # found another individual within infection radius
                        p_test = Epidemic.world[self.position[0] + i][self.position[1] + j]
                        if not p_test.infected and p_test.population == self.population:    # p_test can only be infected if it is healthy and not immune and belongs to same population
                            p_test.infected = np.random.choice([0, 1], p=[1-infection_risk, infection_risk])    # randomly decide whether p_test gets infected based on infection_risk
                            if p_test.infected:
                                Epidemic.infected_people.append(p_test)     # add p_test to infected_people list
                                Epidemic.healthy_people.remove(p_test)  # remove p_test from healthy_people list
                                Epidemic.n_daily_infections[Epidemic.day - 1] += 1  # update number of daily infections for current day
                                p_test.speed = speed_sick   # set p_test's speed to speed_sick

        # recovery:
        if self.infected_days == self.recovery_time:    # infected individual has survived recovery time
            if acquired_immunity:
                self.infected = 2   # make individual immune
                Epidemic.recovered_people.append(self)  # add individual to recovered_people list (only if immune)
            else:
                self.infected = 0   # make individual healthy
            Epidemic.infected_people.remove(self)   # remove individual from infected_people list
            Epidemic.healthy_people.append(self)    # add individual to healthy people list (contains immune and non-immune people)
            self.infected_days = 0  # reset infected days counter
            self.speed = speed_healthy  # set individual's speed back to speed_healthy

        # death:
        if self.infected_days >= self.incubation_period:    # individual has been infected longer than the incubation period
            if np.random.choice([0, 1], p=[1-Epidemic.death_risk, Epidemic.death_risk]):     # randomly decide whether individual dies based on death_risk
                self.infected = 3   # set infected status to dead
                Epidemic.infected_people.remove(self)   # remove individual from infected_people list
                Epidemic.dead_people.append(self)   # add individual to dead_people list
                Epidemic.n_daily_deaths[Epidemic.day-1] += 1    # update daily deaths for current day

    # travel method - used to move individual from one population to another:
    def travel(self):
        for i in range(2):  # move in direction of destination
            if self.position[i] < self.destination[i] - travel_speed:
                self.position[i] += travel_speed
            elif self.position[i] > self.destination[i] + travel_speed:
                self.position[i] -= travel_speed
        if self.destination[0] - travel_speed <= self.position[0] <= self.destination[0] + travel_speed and self.destination[1] - travel_speed <= self.position[1] <= self.destination[1] + travel_speed:   # arrived within travel_speed pixels of destination
            if not Epidemic.world[self.position[0]][self.position[1]]:  # is destination location occupied by another individual?
                self.travelling = False     # terminate transit
                self.destination.clear()    # remove information about destination location
                Epidemic.travelling_people.remove(self)     # remove individual from travelling_people list
                Epidemic.world[self.position[0]][self.position[1]] = self   # put individual back in world matrix

        # draw travelling people:
        particle_rect = pygame.Rect(self.position[0], self.position[1], width, width)   # create pygame.Rect object to display individual on screen
        if self.infected == 2:
            pygame.draw.rect(Epidemic.screen, blue, particle_rect, 0)
        elif self.infected == 1:
            pygame.draw.rect(Epidemic.screen, red, particle_rect, 0)
        elif self.infected == 3:
            pygame.draw.rect(Epidemic.screen, grey, particle_rect, 0)
        else:
            pygame.draw.rect(Epidemic.screen, white, particle_rect, 0)


    # initialise_world classmethod - called once at the start of the simulation (creates all individuals):
    @classmethod
    def initialise_world(cls, n):
        for i in cls.populations.squares:   # distribute n individuals equally among all population squares
            for j in range((n-1)//len(cls.populations.squares)):
                cls.people.append(cls(1, i))   # add each created individual to people list
        cls.people.append(cls(2, cls.populations.squares[0]))   # add one infected individual

    # update_world classmethod - called each iteration to update the simulation (calls update_position, update_infection and travel methods):
    @classmethod
    def update_world(cls):
        for i in cls.people:    # update position for all individuals that aren't travelling
            if not i.travelling:
                i.update_position()

        for i in cls.infected_people:   # update infection status of all individuals
            i.update_infection()

        if number_of_populations > 1:   # only call travel method if at least two separate populations exist
            for i in cls.travelling_people:     # update position for all travelling individuals
                i.travel()
            if np.random.choice([True, False], p=[daily_travellers/day_length, 1-daily_travellers/day_length]):     # randomly decide whether an individual will start to travel next iteration
                okay = False
                while not okay:     # randomly select an individual from people list and check whether they aren't already travelling or dead
                    traveller = Epidemic.people[np.random.randint(0, len(Epidemic.people))]
                    if not traveller.travelling and traveller.infected != 3:
                        okay = True
                traveller.travelling = True     # set travelling status of selected individual to True
                Epidemic.world[traveller.position[0]][traveller.position[1]] = 0    # remove selected individual from world matrix
                population = cls.populations.squares[np.random.choice([i for i in range(len(cls.populations.squares)) if cls.populations.squares[i] != traveller.population])]  # randomly select a population square that the selected individual should travel to
                traveller.destination = list(population.center)     # set center of selected population square as travel destination
                traveller.population = population   # change selected individual's population to newly selected population
                cls.travelling_people.append(traveller)     # add selected individual to travelling_people list

        # update statistical data:
        cls.n_infected.append(len(cls.infected_people))
        cls.n_healthy.append(len(cls.healthy_people))
        cls.n_dead.append(len(cls.dead_people))
        cls.n_recovered.append(len(cls.recovered_people))
        if not cls.iterations % day_length: # only update daily_deaths and daily_infections lists when a full day has passed
            cls.n_daily_deaths.append(0)
            cls.n_daily_infections.append(0)
            cls.day += 1    # increment day counter
        cls.iterations += 1     # increment iterations counter
        cls.populations.draw_squares()  # draw population squares on screen

    # display_statistics classmethod - plots data collected during simulation:
    @classmethod
    def display_statistics(cls, **data):
        n = [i for i in range(cls.iterations + 1)]  # x axis (number of iterations)
        days = [i * day_length for i in range(len(cls.n_daily_deaths))]     # x axis for daily deaths and daily infections (number of days)

        plt.style.use("ggplot")
        for i in data:  # only plot data specified in kwargs
            if data[i]:
                if i == "infected":
                    plt.plot(n, cls.n_infected, label="Total number of infected people", color="red")
                if i == "daily_infected":
                    plt.plot(days, cls.n_daily_infections, label="Infections per day", color="orange")
                if i == "dead":
                    plt.plot(n, cls.n_dead, label="Total deaths", color="black")
                if i == "daily_deaths":
                    plt.plot(days, cls.n_daily_deaths, label="Deaths per day", color="Purple")
                if i == "healthy":
                    plt.plot(n, cls.n_healthy, label="Number of healthy people", color="cyan")
                if i == "recovered":
                    plt.plot(n, cls.n_recovered, label="Number of recovered people", color="blue")

        plt.grid(True)
        plt.legend()
        plt.show()


# initialise epidemic:
pygame.init()
Epidemic.initialise_world(n)
pause = False   # pauses simulation when True

# game loop:
while 1:
    Epidemic.screen.fill(black)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:    # press return to pause/resume simulation
            if event.key == pygame.K_RETURN:
                pause = not pause
                if pause:   # plot data when paused
                    Epidemic.display_statistics(infected=total_number_of_infected_people, daily_infected=daily_number_of_infections, dead=total_number_of_deaths, daily_deaths=daily_number_of_deaths, healthy=number_of_healthy_people, recovered=number_of_recovered_people)

    if not pause:   # run simulation when not paused
        Epidemic.update_world()
        pygame.display.flip()