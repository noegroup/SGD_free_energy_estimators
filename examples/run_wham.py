import argparse
import thermodynamicestimators.utilities.test_case_factory as test_case_factory
import thermodynamicestimators.estimators.WHAM as wham
import thermodynamicestimators.utilities.helper_function as helpers
import matplotlib.pyplot as plt
import torch
from mpl_toolkits.mplot3d import Axes3D


"""
main.py

Prepares histogram data by setting up a potential with biases and using MCMC for sampling.
Uses WHAM to return an estimate of the potential function.
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_name", default='double_well_2D', help="The name of the test problem")
    parser.add_argument("--tolerance", default=10e-2, help="Error tolerance for convergence")
    parser.add_argument("--max_iterations", default=100, help="Maximum number of iterations allowed to converge")

    args = parser.parse_args()


    # generate a test problem with potential, biases, data and histogram bin range
    dataset = test_case_factory.make_test_case(args.test_name, "WHAM")
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=100, shuffle=True)

    estimator = wham.WHAM(dataset)
    optimizer_SGD = torch.optim.SGD(estimator.parameters(), lr=0.01)
    free_energy_SGD, errors_SGD = estimator.estimate(dataloader, optimizer_SGD, max_iterations=20)
    potential_SGD = estimator.get_potential(dataset[:])

    estimator = wham.WHAM(dataset)
    optimizer_ADAM = torch.optim.Adam(estimator.parameters(), lr=0.01)
    free_energy_ADAM, errors_ADAM = estimator.estimate(dataloader, optimizer_ADAM, max_iterations=20)
    potential_ADAM = estimator.get_potential(dataset[:])


    plt.yscale('log')
    plt.plot(errors_SGD, label='SGD error, lr=0.01')
    plt.plot(errors_ADAM, label='ADAM error, lr=0.01')

    plt.legend()
    plt.show()


    if args.test_name == "double_well_1D":
        plt.plot([dataset.potential_function(x) for x in range(100)], label="real potential function", color='g')
        plt.plot(potential_SGD, label="SGD")
        plt.plot(potential_ADAM, label="ADAM")

    if args.test_name == "double_well_2D":
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        x = torch.tensor(range(dataset.histogram_range[0][0], dataset.histogram_range[0][1]))
        y = torch.tensor(range(dataset.histogram_range[1][0], dataset.histogram_range[1][1]))
        X, Y = torch.meshgrid(x, y)

        # real_potential = torch.zeros_like(X)
        # for r, _ in torch.ndenumerate(real_potential):
        #     real_potential[r] = dataset.potential((X[r], Y[r])))

        ax.plot_wireframe(X, Y, potential_SGD - potential_SGD[~torch.isinf(potential_SGD)].mean(), label="SGD", color='b')
        ax.plot_wireframe(X, Y, potential_ADAM - potential_ADAM[~torch.isinf(potential_ADAM)].mean(), label="ADAM", color='r')
        # ax.plot_wireframe(X, Y, real_potential - real_potential.mean(), label="Real potential function", color='g')

    plt.legend()
    plt.show()


if __name__ == "__main__":
    main()