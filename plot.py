
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.stats as st

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

def plot_wealth_distribution(agents, title="No norms", color="gray", save=False):
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
        results_dir = os.path.join(os.path.dirname(__file__), "results")
        os.makedirs(results_dir, exist_ok=True)
        fname = title.lower().replace(" ", "_") + ".png"
        plt.savefig(os.path.join(results_dir, fname))
        print(f"Saved to {os.path.join(results_dir, fname)}")
        plt.close()
    else:
        plt.show()


