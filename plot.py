
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.stats as st


################################################################################################################
# Wealth distribution with gini plots
################################################################################################################

def gini_coefficient(values):
    """Compute Gini index of a list of values (e.g., wealth)."""
    array = np.array(values)
    if np.amin(array) < 0:
        array -= np.amin(array)  # Make non-negative
    array += 1e-8  # Avoid divide by zero
    array = np.sort(array)
    n = len(array)
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * array)) / (n * np.sum(array))

def plot_wealth_distribution(agents, title="No norms", color="gray", save=False, results_dir="results"):
    """Plot wealth histogram with Gini annotation like in the aporophobia paper."""
    wealths = np.array([agent.final_wealth() for agent in agents])

    # Compute Gini and 95% CI using bootstrapping
    gini = gini_coefficient(wealths)
    bootstraps = [gini_coefficient(np.random.choice(wealths, size=len(wealths), replace=True)) for _ in range(1000)]
    gini_std = np.std(bootstraps)
    ci = 1.96 * gini_std

    # Plot histogram
    plt.figure(figsize=(5, 4))
    count, bins, _ = plt.hist(wealths, bins=20, color=color, density=True, alpha=0.7, edgecolor="black")
    sns_kde = True
    try:
        import seaborn as sns
        sns.kdeplot(wealths, color=color, lw=2)
    except ImportError:
        sns_kde = False

    # Annotate Gini index
    gini_text = f"Gini: {gini:.3f} ± {ci:.3f}"
    plt.legend([gini_text], loc="upper right", fontsize=10, frameon=True)
    plt.xlabel("Wealth")
    plt.ylabel("Frequency")
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()

    # Save if needed
    if save:
        fname = title.lower().replace(" ", "_").replace(":","_") + ".png"
        save_plot(results_dir=results_dir, title=fname)
        plt.close()
    else:
        plt.show()


################################################################################################################
# Attribute vs. Another attribute plots (e.g. social tolerance vs. wealth)
################################################################################################################


def save_plot(title, results_dir):
    save_path = os.path.join(results_dir, f"{title}.png")
    plt.savefig(save_path)
    print(f"Plot saved to: {save_path}")
    

def plot_relations(agents, x_fn, y_fn, xlabel="", ylabel="", title="", save_fig=True, results_dir="results"):
    # Gather data for plotting
    tolerance_groups = {}
    for agent in agents:
        tol = x_fn(agent)
        if tol not in tolerance_groups:
            tolerance_groups[tol] = []
        tolerance_groups[tol].append(y_fn(agent))

    # TODO: Confidence interval should be computed for trials of same experimental settings 
    # I think for social tolerance levels we should just show max/mean/min values
    # Compute mean and 95% confidence intervals
    labels = sorted(tolerance_groups.keys())
    means = [np.mean(tolerance_groups[t]) for t in labels]
    stds = [np.std(tolerance_groups[t]) for t in labels]
    cis = [1.96 * std / np.sqrt(len(tolerance_groups[t])) for t, std in zip(labels, stds)]

    # Plot
    plt.figure(figsize=(8, 5))
    plt.errorbar(labels, means, yerr=cis, fmt='o', capsize=5, label="95% CI")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    
    if save_fig:
        save_plot(title, results_dir)
        plt.close()
    else:
        plt.show()
