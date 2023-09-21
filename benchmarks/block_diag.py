import numpy as np
from scipy.sparse import block_diag
from bed_reader import open_bed
import pandas as pd

import gwasprs


BLOCK = 20

# read files

bfile_prefix = "/Users/yuehhua/workspace/DEMO/DEMO_CLF/demo_hg38"
my_bed = open_bed(f"{bfile_prefix}.bed")
metadata = pd.read_csv(f"{bfile_prefix}.csv")


# data

nsample = my_bed.iid_count
nsnp = my_bed.sid_count

# y = np.random.randn(nsample * 3)
genotype = my_bed.read()
covariates = covariates = metadata[["SEX", "AGE"]].values


def hcat_dropna(A, B):
    X = np.concatenate((A, B), axis=1)
    return X[gwasprs.mask.isnonnan(X)]


def dropna_block_diag(genotype, covariates):
    As = [hcat_dropna(genotype[:, i:i+1], covariates) for i in range(genotype.shape[1])]
    return block_diag(As)


# model

X = dropna_block_diag(genotype[:, 0:BLOCK], covariates)
beta = np.random.rand(X.shape[1])
model = gwasprs.LinearRegression(beta)

y_hat = X @ beta

# BLOCK = 10
# In [3]: %timeit X @ beta
# 394 µs ± 64.8 µs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)

# BLOCK = 20
# In [7]: %timeit X @ beta
# 937 µs ± 137 µs per loop (mean ± std. dev. of 7 runs, 1,000 loops each)

# BLOCK = 50
# In [10]: %timeit X @ beta
# 2.73 ms ± 602 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

# BLOCK = 100
# In [13]: %timeit X @ beta
# 5.43 ms ± 627 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

# BLOCK = 200
# In [16]: %timeit X @ beta
# 10.9 ms ± 947 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

# BLOCK = 500
# In [19]: %timeit X @ beta
# 23.6 ms ± 636 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

# BLOCK = 1000
# In [22]: %timeit X @ beta
# 48.3 ms ± 1.03 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

# BLOCK = 2000
# In [59]: %timeit X @ beta
# 116 ms ± 35.5 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

# BLOCK = 3000
# In [63]: %timeit X @ beta
# 244 ms ± 70 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 4000
# In [67]: %timeit X @ beta
# 351 ms ± 54.4 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 5000
# In [55]: %timeit X @ beta
# 481 ms ± 130 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 7500
# In [71]: %timeit X @ beta
# 959 ms ± 291 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 10000
# In [25]: %timeit X @ beta
# 984 ms ± 258 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)


cov = X.T @ X

# BLOCK = 10
# In [28]: %timeit X.T @ X
# 6.38 ms ± 884 µs per loop (mean ± std. dev. of 7 runs, 100 loops each)

# BLOCK = 20
# In [31]: %timeit X.T @ X
# 11.8 ms ± 1.94 ms per loop (mean ± std. dev. of 7 runs, 100 loops each)

# BLOCK = 50
# In [34]: %timeit X.T @ X
# 28.7 ms ± 5.23 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

# BLOCK = 100
# In [37]: %timeit X.T @ X
# 53.8 ms ± 946 µs per loop (mean ± std. dev. of 7 runs, 10 loops each)

# BLOCK = 200
# In [40]: %timeit X.T @ X
# 118 ms ± 11.4 ms per loop (mean ± std. dev. of 7 runs, 10 loops each)

# BLOCK = 500
# In [44]: %timeit X.T @ X
# 336 ms ± 46.9 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 1000
# In [47]: %timeit X.T @ X
# 768 ms ± 43.3 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 2000
# In [60]: %timeit X.T @ X
# 2.22 s ± 589 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 3000
# In [64]: %timeit X.T @ X
# 3.36 s ± 444 ms per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 4000
# In [68]: %timeit X.T @ X
# 5.08 s ± 1.84 s per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 5000
# In [56]: %timeit X.T @ X
# 9 s ± 2.14 s per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 7500
# In [72]: %timeit X.T @ X
# 1min 5s ± 8.23 s per loop (mean ± std. dev. of 7 runs, 1 loop each)

# BLOCK = 10000
# In [50]: %timeit X.T @ X
# 2min 5s ± 20.8 s per loop (mean ± std. dev. of 7 runs, 1 loop each)