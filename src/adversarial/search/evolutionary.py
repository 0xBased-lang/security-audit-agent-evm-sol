"""
Evolutionary Search Algorithm

Genetic algorithm for optimizing attack strategy parameters.
Evolves populations of strategies to maximize profit.
"""

import random
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
import copy


@dataclass
class Individual:
    """Individual in the population (a strategy with specific parameters)"""
    strategy: Any  # StrategyTemplate
    fitness: Decimal = Decimal(0)
    age: int = 0


class EvolutionarySearch:
    """
    Evolutionary Search Algorithm

    Uses genetic algorithms to evolve attack strategies:
    1. Initialize population of random strategies
    2. Evaluate fitness (profit) for each
    3. Select best performers
    4. Create offspring via crossover and mutation
    5. Repeat for N generations

    This is particularly effective for:
    - Parameter optimization (amounts, gas prices, etc.)
    - Finding local optima quickly
    - Exploring large parameter spaces

    Example:
        search = EvolutionarySearch(
            population_size=100,
            mutation_rate=0.1,
            crossover_rate=0.7
        )

        results = search.evolve(
            environment=env,
            agents=attacker_agents,
            iterations=1000
        )
    """

    def __init__(
        self,
        population_size: int = 100,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        elite_size: int = 10,
        tournament_size: int = 5
    ):
        """
        Initialize evolutionary search

        Args:
            population_size: Number of individuals in population
            mutation_rate: Probability of mutating each gene
            crossover_rate: Probability of crossover vs cloning
            elite_size: Number of top individuals to preserve
            tournament_size: Size of tournament for selection
        """
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size
        self.tournament_size = tournament_size

        self.logger = logging.getLogger(__name__)

        # Evolution state
        self.population: List[Individual] = []
        self.generation = 0
        self.best_individual: Individual = None
        self.fitness_history: List[Decimal] = []

    def evolve(
        self,
        environment: Any,
        agents: List[Any],
        iterations: int = 1000,
        parallel: int = 1
    ) -> Dict[str, Any]:
        """
        Run evolutionary algorithm

        Args:
            environment: Simulation environment
            agents: List of attacker agents (provide strategy templates)
            iterations: Number of generations to evolve
            parallel: Number of parallel evaluations (not implemented in MVP)

        Returns:
            Dictionary with results:
                - strategies: List of successful strategies
                - sequences: Attack sequences found
                - metrics: Evolution metrics
        """
        self.logger.info(f"Starting evolutionary search ({iterations} generations)...")

        # Initialize population from agent strategies
        self._initialize_population(agents)

        # Evolution loop
        for gen in range(iterations):
            self.generation = gen

            # Evaluate fitness
            self._evaluate_population(environment)

            # Log progress
            if gen % 50 == 0:
                best_fitness = self.best_individual.fitness if self.best_individual else 0
                avg_fitness = sum(ind.fitness for ind in self.population) / len(self.population)
                self.logger.info(
                    f"Generation {gen}/{iterations}: "
                    f"Best={best_fitness:,.2f}, Avg={avg_fitness:,.2f}"
                )

            # Check termination
            if self._should_terminate():
                self.logger.info(f"Early termination at generation {gen}")
                break

            # Create next generation
            self.population = self._create_next_generation()

        # Final evaluation
        self._evaluate_population(environment)

        # Compile results
        results = self._compile_results()

        self.logger.info(
            f"Evolution complete. Best fitness: {self.best_individual.fitness:,.2f}"
        )

        return results

    def _initialize_population(self, agents: List[Any]):
        """
        Initialize population from agent strategies

        Creates random variations of each agent's strategy
        """
        self.population = []

        strategies_per_agent = self.population_size // len(agents)

        for agent in agents:
            base_strategy = agent.strategy

            for _ in range(strategies_per_agent):
                # Create mutated version
                mutated_strategy = base_strategy.mutate(mutation_rate=0.5)  # High initial mutation
                individual = Individual(strategy=mutated_strategy)
                self.population.append(individual)

        # Fill remaining slots
        while len(self.population) < self.population_size:
            agent = random.choice(agents)
            mutated_strategy = agent.strategy.mutate(mutation_rate=0.5)
            individual = Individual(strategy=mutated_strategy)
            self.population.append(individual)

        self.logger.info(f"Initialized population of {len(self.population)} individuals")

    def _evaluate_population(self, environment: Any):
        """
        Evaluate fitness of all individuals in population

        Fitness = profit from executing strategy
        """
        for individual in self.population:
            try:
                # Execute strategy in environment
                result = individual.strategy.execute(environment)

                # Fitness is the profit
                individual.fitness = result.profit

                # Track best individual
                if not self.best_individual or individual.fitness > self.best_individual.fitness:
                    self.best_individual = copy.deepcopy(individual)

            except Exception as e:
                self.logger.error(f"Strategy evaluation failed: {e}")
                individual.fitness = Decimal(-1000000)  # Large penalty

            individual.age += 1

        # Track fitness history
        if self.best_individual:
            self.fitness_history.append(self.best_individual.fitness)

    def _should_terminate(self) -> bool:
        """Check if evolution should terminate early"""
        # Terminate if no improvement in last 100 generations
        if len(self.fitness_history) >= 100:
            recent_fitness = self.fitness_history[-100:]
            if len(set(recent_fitness)) == 1:  # No change
                return True

        return False

    def _create_next_generation(self) -> List[Individual]:
        """
        Create next generation via selection, crossover, and mutation

        Process:
        1. Elitism: Keep top performers
        2. Selection: Tournament selection
        3. Crossover: Create offspring
        4. Mutation: Mutate offspring
        """
        next_generation = []

        # Step 1: Elitism - preserve best individuals
        sorted_population = sorted(
            self.population,
            key=lambda ind: ind.fitness,
            reverse=True
        )
        elite = sorted_population[:self.elite_size]
        next_generation.extend(copy.deepcopy(elite))

        # Step 2-4: Fill rest of population
        while len(next_generation) < self.population_size:
            # Selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()

            # Crossover
            if random.random() < self.crossover_rate:
                offspring_strategy = parent1.strategy.crossover(parent2.strategy)
            else:
                offspring_strategy = copy.deepcopy(parent1.strategy)

            # Mutation
            if random.random() < self.mutation_rate:
                offspring_strategy = offspring_strategy.mutate(self.mutation_rate)

            offspring = Individual(strategy=offspring_strategy)
            next_generation.append(offspring)

        return next_generation

    def _tournament_selection(self) -> Individual:
        """
        Select individual via tournament selection

        Randomly select tournament_size individuals and return the best
        """
        tournament = random.sample(self.population, self.tournament_size)
        winner = max(tournament, key=lambda ind: ind.fitness)
        return winner

    def _compile_results(self) -> Dict[str, Any]:
        """Compile final results"""
        # Get all strategies with positive fitness
        successful_strategies = [
            {
                'type': ind.strategy.category,
                'profit': float(ind.fitness),
                'success': ind.fitness > 0,
                'fitness': float(ind.fitness),
                'transactions': [],  # Would be populated from execution
                'parameters': ind.strategy.parameters,
                'sequence': []
            }
            for ind in self.population
            if ind.fitness > 0
        ]

        # Sort by fitness
        successful_strategies.sort(key=lambda s: s['profit'], reverse=True)

        return {
            'strategies': successful_strategies,
            'sequences': [],  # Would contain detailed transaction sequences
            'metrics': {
                'total_generations': self.generation + 1,
                'best_fitness': float(self.best_individual.fitness) if self.best_individual else 0,
                'num_successful': len(successful_strategies),
                'fitness_history': [float(f) for f in self.fitness_history]
            }
        }

    def get_best_strategy(self) -> Any:
        """Get the best strategy found"""
        return self.best_individual.strategy if self.best_individual else None

    def get_top_strategies(self, n: int = 10) -> List[Any]:
        """
        Get top N strategies

        Args:
            n: Number of strategies to return

        Returns:
            List of top strategies
        """
        sorted_population = sorted(
            self.population,
            key=lambda ind: ind.fitness,
            reverse=True
        )

        return [ind.strategy for ind in sorted_population[:n]]

    def save_population(self, filepath: str):
        """Save population to file"""
        import json

        data = {
            'generation': self.generation,
            'population_size': len(self.population),
            'best_fitness': float(self.best_individual.fitness) if self.best_individual else 0,
            'individuals': [
                {
                    'strategy': ind.strategy.to_dict(),
                    'fitness': float(ind.fitness),
                    'age': ind.age
                }
                for ind in self.population
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Population saved to {filepath}")

    def load_population(self, filepath: str):
        """Load population from file"""
        import json

        with open(filepath, 'r') as f:
            data = json.load(f)

        self.generation = data['generation']
        # Would reconstruct population from saved data

        self.logger.info(f"Population loaded from {filepath}")
