from thermodynamicestimators.test_cases import potential as potentials
from thermodynamicestimators.utilities import MCMC
import torch
import thermodynamicestimators.test_cases.data_file_manager as file_manager
from thermodynamicestimators.test_cases.test_case import TestCase


def make_test_case(test_name, method):

    dataset = file_manager.load_when_available(test_name, method)
    if dataset is not None:
        return dataset

    if test_name == "double_well_1D":
        test_case = make_double_well_1D_dataset()

    if test_name == "double_well_2D":
        test_case = make_double_well_2D_dataset()


    if method == 'WHAM':
        dataset = test_case.to_wham_dataset()

    if method == "MBAR":
        dataset = test_case.to_mbar_dataset()

    file_manager.save_dataset(dataset, test_name, method)
    return dataset



def make_double_well_1D_dataset():
    potential = potentials.double_well_1D()

    bias_centers = torch.linspace(0, 100, 20)
    biases = [lambda x, r_0=bias_center: potentials.harmonic(x, k=0.1, r_0=r_0) for bias_center in bias_centers]

    sampling_range = torch.tensor([[0, 100]])

    sampler = MCMC.MCMC(sampling_range, max_step=3, n_dimensions=1, n_samples=1000)

    return TestCase(potential, biases, sampler, sampling_range)


def make_double_well_2D_dataset():
    potential = potentials.double_well_2D()

    bias_centers = [(10 * k + 5) / 3 for k in range(1, 8)]

    def bias(r, r_0):
        if len(r.shape) == 1:
            r = r.unsqueeze(0)
        # bias depends only on x value
        x = r[:, 0]

        return potentials.harmonic(x, r_0, k=0.2)

    biases = [(lambda r, r_0=bias_center: bias(r, r_0=r_0)) for bias_center in bias_centers]

    initial_coordinates = torch.tensor([[c, torch.randint(5, 26, size=[1]).item()] for c in bias_centers])
    sampling_range = torch.tensor([[5., 25.], [5., 25.]])
    sampler = MCMC.MCMC(sampling_range, max_step=3, n_dimensions=2, n_samples=10000)

    return TestCase(potential, biases, sampler, sampling_range, initial_coordinates)