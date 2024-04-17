import math
import random
from functools import lru_cache
from typing import Dict, Union


class Animal:
    """
    Animal class. Defines the animal's attributes and its methods.
    """

    # Class Parameters
    w_birth = 0.0
    sigma_birth = 0.0
    beta = 0.0
    eta = 0.0
    a_half = 0.0
    phi_age = 0.0
    w_half = 0.0
    phi_weight = 0.0
    mu = 0.0
    gamma = 0.0
    zeta = 0.0
    xi = 0.0
    omega = 0.0
    F = 0.0

    default_params = {"w_birth": w_birth,
                      "sigma_birth": sigma_birth,
                      "beta": beta,
                      "eta": eta,
                      "a_half": a_half,
                      "phi_age": phi_age,
                      "w_half": w_half,
                      "phi_weight": phi_weight,
                      "mu": mu,
                      "gamma": gamma,
                      "zeta": zeta,
                      "xi": xi,
                      "omega": omega,
                      "F": F}
    weight_check_prob = zeta * (w_birth + sigma_birth)

    def __init__(self, age: int = 0, weight: float = None):
        """
        :param age: Age of the animal. Cannot be negative.
        :param weight: Weight of the animal. Autogenerated from a Gaussian distribution if None.
        """
        self.species = None
        self.is_dead = False
        self.age = age
        self.weight = weight if weight is not None else random.gauss(self.w_birth, self.sigma_birth)
        self._fitness = -1

    def to_json(self):
        props = {"species": self.species,
                 "age": self.age,
                 "weight": self.weight,
                 "fitness": self.fitness,
                 "is_dead": self.is_dead}
        props.update(
            {key: getattr(self, key) for key, value in self.default_params.items()})
        return props

    @property
    def age(self):
        return self._age

    @age.setter
    def age(self, val: int):
        if val < 0:
            raise ValueError('Age cannot be negative')
        self._age = val
        self.reset_fitness()

    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, val: int):
        if val < 0:
            raise ValueError('Weight cannot be negative')
        self._weight = val
        self.reset_fitness()

    def reset_fitness(self):
        """
        Reset the fitness of the animal
        """
        self._fitness = -1

    @classmethod
    def set_params(cls, params: Dict[str, Union[int, float]]):
        """
        Set the parameters of the class.

        :param params: Parameters to be updated
        """
        for key, value in params.items():
            if key not in cls.default_params.keys():
                raise ValueError(f"Invalid parameter: {key}")
            if not (type(value) == float or type(value) == int):
                raise ValueError(f"Value {value} for key {key} is not a float or an integer.")
        for key, value in params.items():
            setattr(cls, key, value)
        cls.weight_check_prob = cls.zeta * (cls.w_birth + cls.sigma_birth)

    @classmethod
    def reset_params(cls):
        """
        Reset the parameters of the animal
        """
        for key, value in cls.default_params.items():
            setattr(cls, key, value)
        cls.weight_check_prob = cls.zeta * (cls.w_birth + cls.sigma_birth)

    @classmethod
    @lru_cache(maxsize=None)
    def _get_fitness_age_part(cls, age, phi_age, a_half):
        return 1 / (1 + math.exp(phi_age * (age - a_half)))

    def _calculate_fitness(self):
        age_part = self._get_fitness_age_part(self.age, self.phi_age, self.a_half)
        weight_part = 1 / (1 + math.exp(-1 * self.phi_weight * (self.weight - self.w_half)))
        self._fitness = age_part * weight_part

    @property
    def fitness(self) -> float:
        """
        Calculate and return the fitness of the animal

        .. math::
            \\Phi = \\left\\{\\begin{matrix}0 & \\ w \\leq 0
            \\\\
            q^{+}(a,a_{\\frac{1}{2}}, \\phi_{age})\\times q^{-}(w,w_{\\frac{1}{2}},
             \\phi_{weight}) & else\\
            \\end{matrix}\\right.
            \\\\
            where \\ q^{\\pm }(x,x_{\\frac{1}{2}}, \\phi)=\\frac{1}{1+e^{\\pm\\phi
            ( x-x_{\\frac{1}{2}})}}, and \\ 0\\leq \\Phi \\leq 1
        """
        # If the fitness is less than zero, it's been reset and needs to be calculated again.
        if self._fitness < 0:
            # If weight is less than zero, animal is dead, set fitness to zero.
            if self.weight <= 0:
                self._fitness = 0
            else:
                self._calculate_fitness()
        return self._fitness

    def feeding(self, feed: Union[int, float]) -> Union[int, float]:
        """
        Feed the animal. Which causes a weight increase.

        :param feed: The amount of 'feed' to be eaten.
        :return: The amount of feed actually eaten.
        """
        # The animal can only eat upto it's appetite F at a time.
        eaten = min(self.F, feed)
        # Update the weight
        self.weight += self.beta * eaten
        return eaten

    def give_birth(self, num_animals: int):
        """
        Method for an animal to give birth.
        The probability of giving birth to an offspring in one year is

        .. math::
            p = min(1, \\gamma \\times \\Phi \\times \\left( N-1 \\right ))

        The probability of giving birth is also dependent on weight,
        where the probability of birth is zero if

        .. math::
            w < \\zeta (w_{birth}+\\sigma_{birth})

        The probability of giving birth is also
        dependent the mother's weight loss when giving birth.
        If the mother were to lose more weight than her own
        weight the probability of birth is zero.

        .. math::
            w_{mother} < \\xi * w_{child}

        :param num_animals: Number of animals of the same species in the cell the animal is in.
        :return: An object for the child
        """
        if random.random() < min(1.0, self.gamma * self.fitness * (num_animals - 1)):
            # The probability of birth is 0 if the weight w < zeta(w_birth + sigma_birth)
            if self.weight > self.weight_check_prob:
                child = type(self)()
                # Child is only born if mother doesn't lose more than
                # her own weight during the birth
                if self.weight >= (weight_loss := self.xi * child.weight):
                    self.weight -= weight_loss
                    return child
                else:
                    # print('Mother loses more than her own weight', self.weight, wt_chk)
                    return None

    def aging(self):
        """
        Age the animal by 1 year
        """
        self.age += 1

    def lose_weight(self):
        """
        Animal loses weight every year by eta times its own weight.
        """
        self.weight -= self.eta * self.weight

    def death(self):
        """
        Check if an animal will die.
        An animal dies if it's weight is zero or with a probability of

        .. math::
            p = \\omega(1-\\Phi)

        :return: animals dead flag
        """
        if self.weight == 0 or random.random() < self.omega * (1 - self.fitness):
            self.is_dead = True
        return self.is_dead

    def migrate(self):
        """An animal will migrate with probability mu times its fitness"""
        if random.random() < self.mu * self.fitness:
            return True
        else:
            return False