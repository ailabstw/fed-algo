from abc import ABCMeta

import numpy as np
from jax import numpy as jnp
from jax import pmap
from scipy.sparse import issparse

from . import linalg, stats, utils


class LinearModel(object, metaclass=ABCMeta):
    def __init__(self) -> None:
        raise NotImplementedError

    def predict(self, X: 'np.ndarray[(1, 1), np.floating]'):
        raise NotImplementedError


class LinearRegression(LinearModel):
    """A class for linear regression

    Args:
        beta ('np.ndarray[(1,), np.floating]', optional): _description_. Defaults to None.
        XtX ('np.ndarray[(1, 1), np.floating]', optional): _description_. Defaults to None.
        Xty ('np.ndarray[(1,), np.floating]', optional): _description_. Defaults to None.
    """

    def __init__(self, beta = None, XtX = None, Xty = None, algo=linalg.CholeskySolver(), include_bias=False) -> None:
        if beta is None:
            if XtX is None or Xty is None:
                raise ValueError("Must provide XtX and Xty, since beta is not provided.")

            if isinstance(algo, linalg.QRSolver):
                raise ValueError("QRSolver is not supported in constructor.")

            self.__beta = algo(XtX, Xty)
        else:
            self.__beta = beta

        self.__include_bias = include_bias

    @property
    def coef(self):
        return self.__beta

    def dof(self, nobs):
        """Degrees of freedom

        Args:
            nobs (int, np.ndarray): Number of observations

        Returns:
            int: _description_
        """
        k = self.__beta.shape[0] + self.__include_bias
        return nobs - k

    def predict(self, X: 'np.ndarray[(1, 1), np.floating]'):
        if issparse(X):
            return X @ self.__beta
        else:
            return linalg.mvmul(X, self.__beta)

    @classmethod
    def fit(cls, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]', algo=linalg.CholeskySolver(), include_bias=False):
        if isinstance(algo, linalg.QRSolver):
            beta = algo(X, y)
        else:
            beta = algo(stats.unnorm_autocovariance(X), stats.unnorm_covariance(X, y))
        return LinearRegression(beta = beta, include_bias = include_bias)

    def residual(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]'):
        return y - self.predict(X)

    def sse(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]'):
        res = self.residual(X, y)
        return jnp.vdot(res.T, res)

    def t_stats(self, sse, XtX, dof):
        XtXinv = jnp.linalg.inv(XtX)
        sigma_squared = sse / dof
        vars = (sigma_squared * XtXinv).diagonal()
        std = jnp.sqrt(vars)
        t_stat = self.coef / std
        return t_stat


class BatchedLinearRegression(LinearModel):
    """A class for linear regression for batched data

    Args:
        beta ('np.ndarray[(1,), np.floating]', optional): _description_. Defaults to None.
        XtX ('np.ndarray[(1, 1), np.floating]', optional): _description_. Defaults to None.
        Xty ('np.ndarray[(1,), np.floating]', optional): _description_. Defaults to None.
    """

    def __init__(self, beta = None, XtX = None, Xty = None, algo=linalg.BatchedCholeskySolver(), include_bias=False) -> None:
        if beta is None:
            if XtX is None or Xty is None:
                raise ValueError("Must provide XtX and Xty, since beta is not provided.")

            if isinstance(algo, linalg.QRSolver):
                raise ValueError("QRSolver is not supported in constructor.")

            self.__beta = algo(XtX, Xty)
        else:
            self.__beta = beta

        self.__include_bias = include_bias

    @property
    def coef(self):
        return self.__beta

    def dof(self, nobs):
        """Degrees of freedom

        Args:
            nobs (int, np.ndarray): Number of observations

        Returns:
            int: _description_
        """
        k = self.coef.shape[-1] + self.__include_bias
        return nobs - k

    def predict(self, X: 'np.ndarray[(1, 1, 1), np.floating]', acceleration="single"):
        if acceleration == "single":
            return linalg.batched_mvmul(X, self.coef)
        elif acceleration == "pmap":
            pmap_func = pmap(linalg.batched_mvmul, in_axes = (0, 0), out_axes = 0)
            ncores = utils.jax_cpu_cores()
            batch, nsample, ndims = X.shape
            minibatch, remainder = divmod(batch, ncores)
            A = np.reshape(X[:(minibatch*ncores), :, :], (ncores, minibatch, nsample, ndims))
            a = np.reshape(self.coef[:(minibatch*ncores), :], (ncores, minibatch, ndims))
            Y = np.reshape(pmap_func(A, a), (-1, nsample))

            if remainder != 0:
                B = X[(minibatch*ncores):, :, :]
                b = self.coef[(minibatch*ncores):, :]
                Z = linalg.batched_mvmul(B, b)
                Y = np.concatenate((Y, Z), axis=0)
            return Y
        else:
            raise ValueError(f"{acceleration} acceleration is not supported.")

    @classmethod
    def fit(cls, X: 'np.ndarray[(1, 1, 1), np.floating]', y: 'np.ndarray[(1, 1), np.floating]', algo=linalg.BatchedCholeskySolver(), include_bias=False):
        if isinstance(algo, linalg.QRSolver):
            raise ValueError("QRSolver is not supported.")

        beta = algo(stats.batched_unnorm_autocovariance(X), stats.batched_unnorm_covariance(X, y))
        return BatchedLinearRegression(beta = beta, include_bias = include_bias)

    def residual(self, X: 'np.ndarray[(1, 1, 1), np.floating]', y: 'np.ndarray[(1, 1), np.floating]', acceleration="single"):
        return y - self.predict(X, acceleration=acceleration)

    def sse(self, X: 'np.ndarray[(1, 1, 1), np.floating]', y: 'np.ndarray[(1, 1), np.floating]', acceleration="single"):
        res = self.residual(X, y, acceleration=acceleration)
        return linalg.batched_vdot(res, res)

    def t_stats(self, sse, XtX, dof):
        XtXinv = linalg.batched_inv(XtX)
        sigma_squared = jnp.expand_dims(jnp.expand_dims(sse / dof, -1), -1)
        vars = linalg.batched_diagonal(sigma_squared * XtXinv)
        std = jnp.sqrt(vars)
        t_stat = self.coef / std
        return t_stat


class BlockedLinearRegression(LinearModel):
    """A class for blocked linear regression

    Args:
        beta ('np.ndarray[(1,), np.floating]', optional): _description_. Defaults to None.
        XtX ('np.ndarray[(1, 1), np.floating]', optional): _description_. Defaults to None.
        Xty ('np.ndarray[(1,), np.floating]', optional): _description_. Defaults to None.
    """

    def __init__(self, beta = None, XtX = None, Xty = None, nmodels: int = 1, algo=linalg.CholeskySolver()) -> None:
        if beta is None:
            if XtX is None or Xty is None:
                raise ValueError("Must provide XtX and Xty, since beta is not provided.")

            if isinstance(algo, linalg.QRSolver):
                raise ValueError("QRSolver is not supported in constructor.")

            if XtX.shape[0] % nmodels != 0:
                raise ValueError(f"Dimension of XtX ({XtX.shape[0]}) is not divisible by number of models ({nmodels}).")

            self.__beta = algo(XtX, Xty)
        else:
            if beta.shape[0] % nmodels != 0:
                raise ValueError(f"Dimension of beta ({beta.shape[0]}) is not divisible by number of models ({nmodels}).")

            self.__beta = beta

        self.__nmodels = nmodels

    @property
    def nmodels(self):
        return self.__nmodels

    @property
    def coef(self):
        return self.__beta

    @property
    def coef_dim(self):
        return self.__beta.shape[0] // self.nmodels

    def dof(self, nobs):
        """Degrees of freedom

        Args:
            nobs (int, np.ndarray): Number of observations

        Returns:
            int: _description_
        """
        k = self.coef_dim
        return nobs - k

    def predict(self, X: 'np.ndarray[(1, 1), np.floating]'):
        return X @ self.__beta

    @classmethod
    def fit(cls, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]', nmodels: int = 1, algo=linalg.CholeskySolver()):
        if isinstance(algo, linalg.QRSolver):
            beta = algo(X, y)
        else:
            beta = algo((X.T @ X).toarray(), X.T @ y)
        return BlockedLinearRegression(beta = beta, nmodels = nmodels)

    def residual(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]'):
        return y - self.predict(X)

    def sse(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]', nobss):
        res = self.residual(X, y)
        block_starts = np.cumsum(np.insert(nobss, 0, [0.]))
        sse = np.array([res[block_starts[i]:block_starts[i+1]].T @ res[block_starts[i]:block_starts[i+1]] for i in range(len(block_starts)-1)])
        return sse

    def t_stats(self, sse, XtX, dof):
        XtXinv = np.linalg.inv(XtX)
        sigma_squared = sse / dof
        vars = sigma_squared * XtXinv
        std = np.sqrt(vars.diagonal())
        t_stat = self.coef / std
        return t_stat


class LogisticRegression(LinearModel):
    def __init__(self, beta = None) -> None:
        self.__beta = beta

    def predict(self, X: 'np.ndarray[(1, 1), np.floating]'):
        predicted_y = linalg.logistic_predict(X, self.__beta)
        return jnp.expand_dims(predicted_y, -1)

    def fit(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]'):
        grad = self.gradient(X, y)
        H = self.hessian(X)
        self.__beta = self.beta(grad, H)

    def residual(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]'):
        return jnp.expand_dims(y, -1) - self.predict(X)

    def gradient(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]'):
        return linalg.mvmul(X.T, self.residual(X, y))

    def hessian(self, X: 'np.ndarray[(1, 1), np.floating]'):
        return linalg.logistic_hessian(X, self.predict(X))

    def loglikelihood(self, X: 'np.ndarray[(1, 1), np.floating]', y: 'np.ndarray[(1,), np.floating]'):
        return linalg.logistic_loglikelihood(X, self.predict(X), y)

    def beta(self, gradient, hessian, solver=linalg.CholeskySolver()):
        # solver calculates H^-1 grad in faster way
        return jnp.expand_dims(self.__beta, -1) + solver(hessian, gradient)


class BatchedLogisticRegression(LinearModel):
    def __init__(self, beta=None, acceleration="single") -> None:
        self.__beta = beta
        self.acceleration = acceleration

    def predict(self, X):
        if self.acceleration == "single":
            predicted_y = 1 / (1 + jnp.exp(-linalg.batched_mvmul(X, self.__beta)))
            return jnp.expand_dims(predicted_y, -1)

        elif self.acceleration == "pmap":
            pmap_func = pmap(linalg.batched_logistic_predict, in_axes=(0,0), out_axes=0)
            ncores = utils.jax_cpu_cores()
            batch, nsample, ndims = X.shape
            minibatch, remainder = divmod(batch, ncores)
            A = np.reshape(X[:(minibatch*ncores), :, :], (ncores, minibatch, nsample, ndims))
            a = np.reshape(self.__beta[:(minibatch*ncores), :], (ncores, minibatch, ndims))
            Y = np.reshape(pmap_func(A, a), (-1, nsample))

            if remainder != 0:
                B = X[(minibatch*ncores):, :, :]
                b = self.__beta[(minibatch*ncores):, :]
                Z = linalg.batched_logistic_predict(B, b)
                Y = np.concatenate((Y, Z), axis=0)
            return jnp.expand_dims(Y, -1)
        else:
            raise ValueError(f"{self.acceleration} acceleration is not supported.")

    def fit(self, X, y):
        grad = self.gradient(X, y)
        H = self.hessian(X)
        self.__beta = self.beta(grad, H)

    def residual(self, X, y):
        return linalg.batched_logistic_residual(y, self.predict(X))

    def gradient(self, X, y):
        return linalg.batched_logistic_gradient(X, self.residual(X,y))

    def hessian(self, X):
        return linalg.batched_logistic_hessian(X, self.predict(X))

    def loglikelihood(self, X, y):
        return linalg.batched_logistic_loglikelihood(X, y, self.predict(X))

    def beta(self, gradient, hessian, solver=linalg.BatchedCholeskySolver()):
        try:
            return self.__beta + solver(hessian, gradient)
        except:
            solver = linalg.BatchedInverseSolver()
            return self.__beta + solver(hessian, gradient)


def add_bias(X: np.ndarray, axis=1):
    dims = list(X.shape)
    dims[axis] = 1
    bias = np.ones(dims)
    return np.concatenate((bias, X), axis=axis)
