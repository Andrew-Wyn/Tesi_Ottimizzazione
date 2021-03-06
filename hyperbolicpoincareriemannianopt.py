# -*- coding: utf-8 -*-
"""HyperbolicPoincareRiemannianOpt.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1BPzuBGWZIfdsUZMq3CED6G1Ux-8JtzJW

# Import
"""

import numpy as np
from random import random
import math
from itertools import compress

import matplotlib.pyplot as plt
# from numpy import linalg as LA
import numpy.linalg as la
from sklearn.linear_model import HuberRegressor
from sklearn.preprocessing import StandardScaler

!pip install git+https://github.com/pymanopt/pymanopt
import pymanopt
from pymanopt.manifolds.manifold import Manifold

"""# Poincare Ball"""

class PoincareBall(Manifold):
    def __init__(self, n, k):
        self.k = k
        self.n = n
        self.dimension = k*n
        super().__init__(
            "{} PoincareBall over R^{}".format(self.k, self.n), self.dimension,
            )
        
    def _squeeze(self, X):
        if self.k == 1 and len(X.shape) > 1:
            return np.squeeze(X, axis=1)
        else:
            return X

    def _pack(self, X):
        if len(X.shape) == 1:
            return np.expand_dims(X, axis=1)
        else:
            return X

    def conformal_factor(self, X):
        return 2/(1 - np.sum(X*X, axis=0))

    def mobius_add(self, X, Y):
        X = self._pack(X)
        Y = self._pack(Y)
        x_dot_y = np.sum(X*Y, axis=0)
        x_norm_q = np.sum(X*X, axis=0)
        y_norm_q = np.sum(Y*Y, axis=0)

        num = (1 + 2*x_dot_y + y_norm_q)*X + (1 - x_norm_q)*Y
        
        den = 1 + 2*x_dot_y + x_norm_q*y_norm_q

        return self._squeeze(num/den)

    def typicaldist(self):
        return self.dim / 8

    def inner(self, X, G, H):
        X = self._pack(X)
        G = self._pack(G)
        H = self._pack(H)
        return sum(np.sum(G*H, axis=0) * self.conformal_factor(X)**2)

    def proj(self, X, G):
        # Identity map since the embedding space is the tangent space R^n
        return self._squeeze(G)

    def norm(self, X, G):
        return math.sqrt(self.inner(X, G, G))

    def rand(self):
        isotropic = np.random.standard_normal(size=(self.n, self.k))
        isotropic = isotropic / la.norm(isotropic, axis=0)
        radius = np.random.rand(self.k) ** (1 / self.n)
        x = isotropic * radius
        return self._squeeze(x)

    def randvec(self, X):
        X = self._pack(X)
        v = np.random.rand(self.n, self.k)
        v = v / self.norm(X, v)
        return self._squeeze(v)

    def zerovec(self, X):
        return np.zeros(X.shape)

    def dist(self, X, Y):
        X = self._pack(X)
        Y = self._pack(Y)
        norms2x = np.sum(X*X, axis=0)
        norms2y = np.sum(Y*Y, axis=0)
        norms2diff = np.sum((X - Y)*(X - Y), axis=0)
        #a = max(
        #    1,
        #    1 + 2*(norms2diff / ((1-norms2x)*(1-norms2y))),
        #   )
        return math.sqrt(np.sum(np.arccosh(1 + 2*(norms2diff / ((1-norms2x)*(1-norms2y))))**2))

    def egrad2rgrad(self, X, G):
        X = self._pack(X)
        G = self._pack(G)
        factor_q = self.conformal_factor(X)**2
        return self._squeeze(G/factor_q)

    def ehess2rhess(self, X, G, H, U):
        X = self._pack(X)
        G = self._pack(G)
        H = self._pack(H)
        U = self._pack(U)
        factor = self.conformal_factor(X)
        return self._squeeze((U * np.sum(G*X, axis=0) - G * np.sum(U*X, axis=0)
                - X * np.sum(U*G, axis=0) + H/factor)/factor)

    def retr(self, X, U):
        return self.exp(X, U)

    def exp(self, X, U):
        X = self._pack(X)
        U = self._pack(U)
        norm_u = la.norm(U, axis=0)
        factor = (1 - np.sum(X*X, axis=0))
        # avoid division by 0
        tmp = np.tanh(norm_u/factor) * (U/((norm_u + (norm_u == 0))))
        return self.mobius_add(X, tmp)

    def log(self, X, Y):
        X = self._pack(X)
        Y = self._pack(Y)
        a = self.mobius_add(-X, Y)
        b = la.norm(a, axis=0)

        factor = 1 - np.sum(X*X, axis=0)
        return self._squeeze(a * factor * np.arctanh(b) / b)

    def transp(self, X1, X2, G):
        return G

    def pairmean(self, X, Y):
        return self.exp(X, self.log(X, Y) / 2)

"""# Hyperboloid"""

class Hyperboloid(Manifold):
    def __init__(self, n, k):
        self.n = n
        self.k = k
        self.dimension = n * k
        super().__init__(
            "{} Hyperboloid over R^{}:1".format(k, n), self.dimension,
            )

    def _squeeze(self, X):
        if self.k == 1 and len(X.shape) > 1:
            return np.squeeze(X, axis=1)
        else:
            return X

    def _pack(self, X):
      if len(X.shape) == 1:
        return np.expand_dims(X, axis=1)
      else:
        return X

    def inner_minkowski_columns(self, U, V):
        U = self._pack(U)
        V = self._pack(V)
        return self._squeeze(np.array(
              [
                  np.dot(U[:, i][:-1], V[:, i][:-1]) - U[:, i][-1]*V[:, i][-1]
                  for i in range(self.k)
              ]
              ))

    def typicaldist(self):
        return math.sqrt(self.dim)

    def inner(self, X, U, V):
        U = self._pack(U)
        V = self._pack(V)
        return np.sum(self.inner_minkowski_columns(U, V))

    def proj(self, X, G):
        X = self._pack(X)
        G = self._pack(G)
        inners = self.inner_minkowski_columns(X, G)
        return self._squeeze(G + X*inners)

    def norm(self, X, G):
        return math.sqrt(max(0, self.inner(X, G, G)))

    def rand(self):
        ret = np.zeros((self.n+1, self.k))
        x0 = np.random.normal(size=(self.n, self.k))
        x1 = np.sqrt(1 + np.sum(x0 * x0, axis=0))
        ret[:-1, :] = x0
        ret[-1, :] = x1
        return self._squeeze(ret)

    def randvec(self, X):
        X = self._pack(X)
        U = self.proj(X, np.random.rand(X.shape[0], X.shape[1]))
        return self._squeeze(U / self.norm(X, U))

    def zerovec(self, X):
        return np.zeros(X.shape)

    def _dists(self, X, Y):
        X = self._pack(X)
        Y = self._pack(Y)
        alpha = -self.inner_minkowski_columns(X, Y)
        alpha[alpha < 1] = 1
        return np.arccosh(alpha)

    def dist(self, X, Y):
        X = self._pack(X)
        Y = self._pack(Y)
        return self._squeeze(la.norm(self._dists(X, Y)))

    def egrad2rgrad(self, X, G):
        X = self._pack(X)
        G = self._pack(G)
        G[-1, :] = -G[-1, :]
        return self.proj(X, G)

    def ehess2rhess(self, X, G, H, U):
        X = self._pack(X)
        G = self._pack(G)
        H = self._pack(H)
        U = self._pack(U)
        G[-1, :] = -G[-1, :]
        H[-1, :] = -H[-1, :]
        inners = self.inner_minkowski_columns(X, G)
        return self.proj(X, U*inners + H)

    def retr(self, X, U):
        X = self._pack(X)
        U = self._pack(U)
        return self._squeeze(self.exp(X, U))

    def exp(self, X, U):
        X = self._pack(X)
        U = self._pack(U)
        # compute the individual minkowski norm for each individual column of U
        mink_inners = self.inner_minkowski_columns(U, U)
        vnormmf = np.vectorize(lambda x: math.sqrt(max(0, x)))
        mink_norms = vnormmf(mink_inners)
        a = np.sinh(mink_norms)/mink_norms
        a[np.isnan(a)] = 1
        return self._squeeze(np.cosh(mink_norms)*X + U*a)

    def log(self, X, Y):
        X = self._pack(X)
        Y = self._pack(Y)
        d = self._dists(X, Y)
        a = d/np.sinh(d)
        a[np.isnan(a)] = 1
        return self._squeeze(self.proj(X, Y*a))

    def transp(self, X1, X2, G):
        X1 = self._pack(X1)
        X2 = self._pack(X2)
        G = self._pack(G)
        return self._squeeze(self.proj(X2, G))

    def pairmean(self, X, Y):
        X = self._pack(X)
        Y = self._pack(Y)
        return self._squeeze(self.exp(X, self.log(X, Y), 1/2))

"""# Derivative of the cost function"""

# --- Poincare Gradiend
def poincare_dist_grad(x, y):
  a = 1 - np.dot(x, x)
  b = 1 - np.dot(y, y)
  c = 1 + (2/(a*b))*(np.dot(x-y, x-y))
  
  return 4/(b*math.sqrt(c**2-1))*(((np.dot(y,y) - 2*np.dot(x, y) + 1)/(a**2))*x - y/a)


def frechet_mean_poincare_grad(psi, x_set, manifold):
  res = 0
  for x_i in x_set:
    res += manifold.dist(psi, x_i)*poincare_dist_grad(psi, x_i)
  return res*2/(len(x_set))


def frechet_mean_poincare_rgrad(psi, x_set, manifold):
  egrad = frechet_mean_poincare_grad(psi, x_set, manifold)
  return manifold.egrad2rgrad(psi, egrad)


# --- Hyperboloid Gradient
def frechet_mean_hyperboloid_grad(theta, x_set, manifold):
  res = 0
  for x_i in x_set:
    x_i_g = x_i.copy()
    x_i_g[-1] = -x_i_g[-1] # gradiente euclideo di prodotto di minkowski
    res += -(manifold.dist(theta, x_i) * (manifold.inner_minkowski_columns(theta, x_i)**2 - 1)**(-1/2)) * x_i_g
  res = res*2/(len(x_set))
  return res


def frechet_mean_hyperboloid_rgrad(theta, x_set, manifold):
  egrad = frechet_mean_hyperboloid_grad(theta, x_set, manifold)
  return manifold.egrad2rgrad(theta, egrad)


def frechet_mean(theta, x_set, distance):
  sum_ = 0
  s = len(x_set)
  for x_i in x_set:
    sum_ += distance(theta, x_i)**2
  return sum_/s

def rho(x):
  return x[:-1]/(x[-1]+1)


def inv_rho(y):
  r = np.dot(y,y)
  return np.array(np.append(y[:],[(1+r)/2]))*2/(1-r) 


def plot_alg(seq, x_set, ax):
  x = np.linspace(-1.0, 1.0, 100)
  y = np.linspace(-1.0, 1.0, 100)
  X, Y = np.meshgrid(x,y)
  F = X**2 + Y**2 - 1
  ax.contour(X,Y,F,[0])

  seq = np.array(seq)
  x_set = np.array(x_set)

  ax.scatter(seq[:, 0], seq[:, 1], c="red", marker="x")
  ax.scatter(seq[-1, 0], seq[-1, 1], c="green", marker="^")
  ax.scatter(x_set[:, 0], x_set[:, 1], c="blue", marker="o")


def poincare_dist(x, y):
  return np.arccosh(1 + 2*(np.dot(x-y, x-y)/((1-np.dot(x,x))*(1-np.dot(y,y)))))


def convergence_seq(psi_seq, limit):
  # return [poincare_dist(psi, limit) for psi in psi_seq]
  return [la.norm(psi - limit) for psi in psi_seq]


def plot_seq(x_set, psi_seq, f_seq, g_seq, limit, dim):
  fig = plt.figure(figsize=[12.8, 12.8])
  fig.clf()
  gs = fig.add_gridspec(2, 2)
  ax1 = fig.add_subplot(gs[0, 0])
  ax1.title.set_text("poincar?? ball over complexes (R^2)")
  ax2 = fig.add_subplot(gs[1, 0])
  ax2.title.set_text("error sequence")
  ax3 = fig.add_subplot(gs[0, 1])
  ax3.title.set_text("f sequence")
  ax4 = fig.add_subplot(gs[1, 1])
  ax4.title.set_text("g-norm sequence")

  if dim == 2:
    plot_alg(psi_seq, x_set, ax1)
  conv_seq = convergence_seq(psi_seq, limit)
  ax2.semilogy(conv_seq)
  ax3.semilogy(f_seq)
  g_norm = [la.norm(g) for g in g_seq]
  ax4.semilogy((g_norm))

"""# Optimization Algorithm

## Fixed Lenght Step Size
"""

def optimisation_fixed_lenght(manifold, x_0, f_grad, x_set, learning_rate, max_steps=10, limited=True):
  x_seq = [x_0]
  f_seq = []
  g_seq = []

  k = 0

  while True:
    psi = x_seq[-1]
    g = f_grad(psi, x_set, manifold)

    if la.norm(g) < 10e-10:
      break

    if np.isnan(g).any():
      x_seq = x_seq[:-1]
      break

    new_psi=manifold.exp(psi, -learning_rate*g)

    x_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, manifold.dist))
    g_seq.append(g)

    # forced exit condition
    k = k+1
    if limited and k >= max_steps:
      break
    
  return x_seq, f_seq, g_seq


def optimisation_fl_poincare(psi_0, x_set, learning_rate, max_steps=10, limited=True):
  return optimisation_fixed_lenght(PoincareManifold, psi_0, frechet_mean_poincare_rgrad, x_set, learning_rate, max_steps, limited)


def optimisation_fl_hyperboloid(psi_0, x_set, learning_rate, max_steps=10, limited=True):
  psi_seq, f_seq, g_seq = optimisation_fixed_lenght(HyperboloidManifold, inv_rho(psi_0), frechet_mean_hyperboloid_rgrad, [inv_rho(x_i) for x_i in x_set], learning_rate, max_steps, limited)
  return [rho(psi) for psi in psi_seq], f_seq, g_seq

"""## Armijo"""

def armijo_step_riemannian(manifold, theta, x_set, g_k, sigma, gamma, lambda_):
  h = 0
  while frechet_mean(manifold.exp(theta, -(sigma**h)*lambda_*g_k), x_set, manifold.dist) > frechet_mean(theta, x_set, manifold.dist) + gamma*(sigma**h)*lambda_*manifold.inner(theta, g_k, -g_k):
    h += 1
  return h


def armijo_optimization(manifold, x_0, f_grad, x_set, sigma, gamma, lambda_, max_steps=10):
  x_seq = [x_0]
  f_seq = []
  g_seq = []

  k = 0

  while True:
    x_k = x_seq[-1]
    g_k = f_grad(x_k, x_set, manifold)
    if np.isnan(g_k).any():
      x_seq = x_seq[:-1]
      break
    if la.norm(g_k) < 10e-10:
      break

    h_k = armijo_step_riemannian(manifold, x_k, x_set, g_k, sigma, gamma, lambda_)
    new_psi = manifold.exp(x_k, -(sigma**h_k)*lambda_*g_k)
    
    x_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, manifold.dist))
    g_seq.append(g_k)

    # forced exit condition
    k = k+1
    if k >= max_steps:
      break

  return x_seq, f_seq, g_seq


def armijo_poincare(psi_0, x_set, sigma, gamma, lambda_, max_steps=10):
  return armijo_optimization(PoincareManifold, psi_0 , frechet_mean_poincare_rgrad, x_set, sigma, gamma, lambda_, max_steps)


def armijo_hyperboloid(psi_0, x_set, sigma, gamma, lambda_, max_steps=10):
  psi_seq, f_seq, g_seq = armijo_optimization(HyperboloidManifold, inv_rho(psi_0), frechet_mean_hyperboloid_rgrad, [inv_rho(x_i) for x_i in x_set], sigma, gamma, lambda_, max_steps)
  return [rho(psi) for psi in psi_seq], f_seq, g_seq

"""## Barzilai Borwein"""

def RBB(manifold, x_0, f_grad, x_set, a_min, a_max, max_steps=100):
  x_seq = [x_0]
  f_seq = []
  g_seq = []

  a_BB = a_min

  k = 0

  g_k = f_grad(x_0, x_set, manifold)
  while True:
    if la.norm(g_k) < 10e-10:
      break

    x_k = x_seq[-1]

    a_k = a_BB
    new_psi = manifold.exp(x_k, -a_k*g_k)
    new_g = f_grad(new_psi, x_set, manifold)

    x_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, manifold.dist))
    g_seq.append(g_k)
    
    s_k = -a_k*manifold.transp(x_k, new_psi, g_k)
    y_k = new_g + s_k/a_k

    tmp = manifold.inner(new_psi, s_k, y_k)
    if tmp > 0:
      new_tau = manifold.inner(new_psi, s_k, s_k)/(tmp)
      a_BB = min(a_max, max(a_min, new_tau))
    else:
      a_BB = a_max

    # forced exit condition
    k = k+1
    if k >= max_steps:
      break
    
    g_k = new_g

  return x_seq, f_seq, g_seq


def RBB_poincare(psi_0, x_set, a_min, a_max, max_steps=100):
  return RBB(PoincareManifold, psi_0, frechet_mean_poincare_rgrad, x_set, a_min, a_max, max_steps)


def RBB_hyperboloid(psi_0, x_set, a_min, a_max, max_steps=100):
  psi_seq, f_seq, g_seq = RBB(HyperboloidManifold, inv_rho(psi_0), frechet_mean_hyperboloid_rgrad, [inv_rho(x) for x in x_set], a_min, a_max, max_steps)
  return [rho(psi) for psi in psi_seq], f_seq, g_seq

"""## L-BFGS"""

def zoom(manifold, f_grad, x_set, f_0, x_0, g_0, p, alpha_lo, alpha_hi, max_iters=20):
  c1 = 10e-4
  c2 = 0.9
  i = 0

  dphi0 = manifold.inner(x_0, g_0, p)

  while True:
    alpha_i = 0.5*(alpha_lo + alpha_hi)
    alpha = alpha_i
    x_i = manifold.exp(x_0, alpha_i*p)
    f_i = frechet_mean(x_i, x_set, manifold.dist)
    g_i = f_grad(x_i, x_set, manifold)
    x_lo = manifold.exp(x_0, alpha_lo*p)
    f_lo = frechet_mean(x_lo, x_set, manifold.dist)

    if f_i > f_0 + c1*alpha_i*dphi0 or f_i >= f_lo:
      alpha_hi = alpha_i
    else:
      dphi = manifold.inner(x_i, g_i, manifold.transp(x_0, x_i, p))
      if abs(dphi) <= -c2*dphi0:
        return alpha_i
      
      if dphi*(alpha_hi-alpha_lo) >= 0:
        alpha_hi = alpha_lo
      
      alpha_lo = alpha_i
    
    if i > max_iters:
      return alpha_i

    i = i+1


def strong_wolfe(manifold, f_grad, x_0, x_set, g_0, p, max_iter=20):
  c1 = 10e-4
  c2 = 0.9
  alpha_max = 2.5
  alpha_im1 = 0
  alpha_i = 1
  i = 0
  f_0 = frechet_mean(x_0, x_set, HyperboloidManifold.dist)
  f_im1 = f_0

  dphi0 = manifold.inner(x_0, g_0, p)

  while True:
    x_i = manifold.exp(x_0, alpha_i*p)
    f_i = frechet_mean(x_i, x_set, manifold.dist)
    g_i = f_grad(x_i, x_set, manifold)

    if f_i > f_0 + c1*dphi0 or (i>1 and f_i >= f_im1):
      return zoom(manifold, f_grad, x_set, f_0, x_0, g_0, p, alpha_im1, alpha_i)
    
    dphi = manifold.inner(x_i, g_i, manifold.transp(x_0, x_i, p))

    if abs(dphi) <= -c2*dphi0:
      return alpha_i

    if dphi >= 0:
      return zoom(manifold, f_grad, x_set, f_0, x_0, g_0, p, alpha_i, alpha_im1)

    alpha_im1 = alpha_i
    f_im1 = f_i;
    alpha_i = alpha_i + 0.8*(alpha_max-alpha_i)
  
    if i >= max_iter:
      return alpha_i

    i = i+1


def choice_dir_LBFGS(manifold, l, k, x_k, g_k, s_seq, y_seq, p_seq, gamma_seq):
  q = g_k
  alpha = []

  for i in reversed(range(k-l-1)):
    a_i = p_seq[i]*manifold.inner(x_k, s_seq[i], q)
    q = q - a_i*y_seq[i]
    alpha.append(a_i)
  alpha.reverse()

  H = gamma_seq[-1] * np.eye(g_k.shape[0])
  z = np.dot(H, q)
  for i in range(k-l-1):
    b = p_seq[i]*manifold.inner(x_k, y_seq[i], z)
    z = z + s_seq[i]*(alpha[i] - b)
  return z


def LBFGS_poincare(psi_0, f_grad, x_set, M, p_min, p_max, max_steps=100):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []
  s_seq = []
  y_seq = []
  p_seq = []
  gamma_seq = [1]
  
  k = 0
  l = 0

  g_k = f_grad(psi_0, x_set, PoincareManifold)
  g_seq.append(g_k)
  f_seq.append(frechet_mean(psi_0, x_set, PoincareManifold.dist))

  while True:
    if la.norm(g_k) < 10e-10:
      g_seq.append(g_new)
      break

    psi = psi_seq[-1]

    z = choice_dir_LBFGS(PoincareManifold, l, k, psi, g_k, s_seq, y_seq, p_seq, gamma_seq)
    step_size = 1 #strong_wolfe(PoincareManifold, f_grad, psi, x_set, g_k, -z)
    new_psi = PoincareManifold.exp(psi, -step_size*z)
    g_new = f_grad(new_psi, x_set, PoincareManifold)

    psi_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, PoincareManifold.dist))
    g_seq.append(g_new)
    
    g_k = g_new

    tmp = PoincareManifold.norm(new_psi, PoincareManifold.transp(psi, new_psi, -step_size*z))
    beta_k = 1
    if tmp != 0:
      beta_k = PoincareManifold.norm(psi, -step_size*z)/tmp
    s_k = PoincareManifold.transp(psi, new_psi, -step_size*z)
    y_k = g_new/beta_k - PoincareManifold.transp(psi, new_psi, g_k)
    
    gamma_seq.append(PoincareManifold.inner(new_psi, s_k, y_k)/PoincareManifold.inner(new_psi, y_k, y_k))

    tmp = PoincareManifold.inner(new_psi, s_k, y_k)
    if tmp > 0:
      new_p = 1/tmp 
      p_k = min(p_max, max(p_min, new_p))
    else:
      p_k = p_max

    l = max(k-M, 0)

    s_seq.append(s_k)
    y_seq.append(y_k)
    p_seq.append(p_k)
    if k>=M:
      s_seq.pop(0)
      y_seq.pop(0)
      p_seq.pop(0)
    
    for i in range(k-l):
      s_seq[i] = PoincareManifold.transp(psi, new_psi, s_seq[i])
      y_seq[i] = PoincareManifold.transp(psi, new_psi, y_seq[i])

    k = k+1
    if k >= max_steps:
      break

  return psi_seq, f_seq, g_seq


def LBFGS_hyperboloid(psi_0, f_grad, x_set, M, p_min, p_max, max_steps=100):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []
  s_seq = []
  y_seq = []
  p_seq = []
  gamma_seq = [1]
  
  l = 0
  k = 0

  x_set_h = [inv_rho(x_i) for x_i in x_set]

  g_k = f_grad(inv_rho(psi_0), x_set_h, HyperboloidManifold)
  g_seq.append(g_k)
  f_seq.append(frechet_mean(psi_0, x_set, PoincareManifold.dist))

  while True:
    if la.norm(g_k) < 10e-10:
      break

    theta = inv_rho(psi_seq[-1])
    
    z = choice_dir_LBFGS(HyperboloidManifold, l, k, theta, g_k, s_seq, y_seq, p_seq, gamma_seq)
    step_size = 1 #strong_wolfe(HyperboloidManifold, f_grad, theta, x_set_h, g_k, -z)
    new_theta = HyperboloidManifold.exp(theta, -step_size*z)
    g_new = f_grad(new_theta, x_set_h, HyperboloidManifold)

    new_psi = rho(new_theta)
    psi_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, PoincareManifold.dist))

    tmp = HyperboloidManifold.norm(new_theta, HyperboloidManifold.transp(theta, new_theta, -step_size*z))
    beta_k = 1
    if tmp != 0:
      beta_k = HyperboloidManifold.norm(theta, -step_size*z)/tmp
    s_k = HyperboloidManifold.transp(theta, new_theta, -step_size*z)
    y_k = g_new/beta_k - HyperboloidManifold.transp(theta, new_theta, g_k)
    
    gamma_seq.append(HyperboloidManifold.inner(new_theta, s_k, y_k)/HyperboloidManifold.inner(new_theta, y_k, y_k))

    tmp = HyperboloidManifold.inner(new_theta, s_k, y_k)
    if tmp > 0:
      new_p = 1/tmp 
      p_k = min(p_max, max(p_min, new_p))
    else:
      p_k = p_max


    l = max(k-M, 0)

    s_seq.append(s_k)
    y_seq.append(y_k)
    p_seq.append(p_k)
    if k>=M:
      s_seq.pop(0)
      y_seq.pop(0)
      p_seq.pop(0)
    
    for i in range(k-l):
      s_seq[i] = HyperboloidManifold.transp(theta, new_theta, s_seq[i])
      y_seq[i] = HyperboloidManifold.transp(theta, new_theta, y_seq[i])

    k = k+1
    if k >= max_steps:
      break

  return psi_seq, f_seq, g_seq

"""# Caricamento e Creazione dei dati"""

def generate_starting_point(x_set):
  psi_0 = np.zeros(x_set.shape[1]) # poincare_points_factory() # calcolare come media dei punti x_set
  for a_i in x_set:
    psi_0 += a_i
  psi_0 /= len(x_set)
  return psi_0


def parse_set_in_list(x_set):
  points = []
  for x in x_set:
    points += x.tolist()
  return points


def format_data_to_save(x_0, x_set, limit):
  dim = x_set.shape[1]
  points = parse_set_in_list(x_set)
  return [dim] + x_0.tolist() + points + limit.tolist()


def save_to_file(to_save_data, file_name="bunch.txt"):
  with open(file_name, "w") as f:
    for data in to_save_data:
      f.write(",".join(str(i) for i in data) + "\n")


def save_bunch_test_set(bunch_set):
  to_save = [format_data_to_save(x_0, x_set, limit) for (x_0, x_set, limit) in bunch_set]
  save_to_file(to_save)


def load_bunch_from_file(file_name="bunch.txt"):
  x_set_s = []
  dim = -1 # dimensione comune a tutto il dataset
  with open(file_name, "r") as f:
    for line in f.readlines():
      line_els = line.split(",")
      dim = int(line_els[0])
      limit = np.array([float(i) for i in line_els[-dim:]])
      x_0 = np.array([float(i) for i in line_els[1:dim+1]])
      x_set = []
      for i in range(dim+1, len(line_els)-dim, dim):
        x_set.append([float(i) for i in line_els[i:i+dim]])
      x_set = np.array(x_set)
      x_set_s.append((x_0, x_set, limit))
  return dim, x_set_s


def create_bunch_test_set(manifold, card_bunch=50, card_x=4):
  bunch_test_set = []
  for i in range(card_bunch):
    print(i/card_bunch * 100, "%")
    x_set = np.array([manifold.rand() for _ in range(card_x)])
    x_0 = generate_starting_point(x_set)
    # TODO: confrontarmi con il prof per il calcolo del limite
    psi_seq, _, _ = optimisation_fl_poincare(x_0, x_set, 0.001, 5000, False)
    limit = psi_seq[-1]
    bunch_test_set.append((x_0, x_set, limit))

  return bunch_test_set

#dim = 2
#PoincareManifold = PoincareBall(dim, 1)
#HyperboloidManifold = Hyperboloid(dim, 1)
#bunch = create_bunch_test_set(PoincareManifold, card_bunch=200, card_x=4)
#save_bunch_test_set(bunch)

dim, bunch = load_bunch_from_file()
PoincareManifold = PoincareBall(dim, 1)
HyperboloidManifold = Hyperboloid(dim, 1)

"""# Test Algorithms"""

def time_to_converge(seq, limit, iter_test, epsilon=1e-4):
  differences = []
  for s in seq:
    diff = s - limit
    differences.append(math.sqrt(np.dot(diff, diff)) < epsilon)
  time_conv = np.argmax(differences)
  if time_conv == 0:
    time_conv = iter_test
  return time_conv


def test_algorithm(algotithm_poincare, algorithm_hyperboloid, bunch_test_set, iter_test, figname, tollerance_outlier=0):
  a = []
  b = []
  
  for (x_0, x_set, limit) in bunch_test_set:
    seq, _, _ = algotithm_poincare(x_0, x_set, iter_test)
    a.append(time_to_converge(seq, limit, iter_test, 1e-5))
    seq, _, _ = algorithm_hyperboloid(x_0, x_set, iter_test)
    b.append(time_to_converge(seq, limit, iter_test, 1e-5))

  mean_conv_a = sum(a)/len(bunch_test_set)
  mean_conv_b = sum(b)/len(bunch_test_set)

  print("Mean convergence Disk:", mean_conv_a)
  print("Mean convergence Iperboloid:", mean_conv_b)

  ab = list(zip(a, b))
  z = [ab.count(i) for i in ab]
  filter = [z_i > tollerance_outlier for z_i in z]
  a_cutted = list(compress(a, filter))
  b_cutted = list(compress(b, filter))

  a_scaler, b_scaler = StandardScaler(), StandardScaler()
  a_train = a_scaler.fit_transform(np.array(a_cutted)[..., None])
  b_train = b_scaler.fit_transform(np.array(b_cutted)[..., None])

  model = HuberRegressor(epsilon=1)
  model.fit(a_train, b_train.ravel())

  ang_coef_lin, t = np.polyfit(a_cutted, b_cutted, 1)
  test_a = np.array([0, iter_test])
  predictions = b_scaler.inverse_transform(
      model.predict(a_scaler.transform(test_a[..., None]))
  )

  ang_coef_huber = (predictions[1] - predictions[0]) / (test_a[1] - test_a[0])

  print("SLOPE Huber Regressor:", ang_coef_huber)
  print("SLOPE Linear Regressor:", ang_coef_lin)
  plt.figure(figsize=(20, 20))
  plt.plot(test_a, ang_coef_lin*np.array(test_a) + t, 'y')
  plt.plot(test_a, predictions, 'r')
  plt.legend([f'Least Square Regression Line, ang. coeff. = {ang_coef_lin:.4f}', 
              f'Huber Regression Line, ang. coeff. = {ang_coef_huber:.4f}'],
             prop={'size': 20})

  plt.scatter(a, b, c=z)
  plt.colorbar()
  plt.xlabel("Step to Converge on Poincare Disk", fontsize=18)
  plt.ylabel("Step to Converge on Hyperboloid", fontsize=18)
  plt.savefig(figname)

def make_fl_curve(algorithm_poincare, algorithm_hyperbolid, X0, X, limit, iter_test, max_iter=100):
  sequence_poincare = []
  sequence_hyper = []

  for i in range(1, iter_test):
    poincare_seq, _, _= algorithm_poincare(X0, X, (i/iter_test), max_iter)
    min_poincare = time_to_converge(poincare_seq, limit, max_iter)
    sequence_poincare.append(min_poincare)
    hyper_seq, _, _ = algorithm_hyperbolid(X0, X, (i/iter_test), max_iter)
    min_hyper = time_to_converge(hyper_seq, limit, max_iter)
    sequence_hyper.append(min_hyper)

  return np.array(sequence_poincare), np.array(sequence_hyper)


def test_one_parameter_optimization(algorithm_poincare, algorithm_hyperbolid, bunch_test_set, iter_test, max_iter=100):
  sequence_poincare = np.zeros(iter_test-1)
  sequence_hyper = np.zeros(iter_test-1)
  for (x_0, x_set, limit) in bunch_test_set:
    fl_poincare_curve, fl_hyper_curve = make_fl_curve(algorithm_poincare, algorithm_hyperbolid, x_0, x_set, limit, iter_test, max_iter)
    sequence_poincare += fl_poincare_curve
    sequence_hyper += fl_hyper_curve
  return sequence_poincare/len(bunch_test_set), sequence_hyper/len(bunch_test_set)

x_0_test, x_set_test, limit_test = bunch[0]
print("limit:", limit_test)

psi_seq_test, f_seq_test, g_seq_test = optimisation_fl_poincare(x_0_test, x_set_test, 0.1, 100)
print("Limit sequence poincare: ", psi_seq_test[-1])
plot_seq(x_set_test, psi_seq_test, f_seq_test, g_seq_test, limit_test, dim)

psi_seq_test, f_seq_test, g_seq_test = optimisation_fl_hyperboloid(x_0_test, x_set_test, 0.26, 100)
print("Limit sequence iperboloide: ", psi_seq_test[-1])
plot_seq(x_set_test, psi_seq_test, f_seq_test, g_seq_test, limit_test, dim)

psi_seq_test, f_seq_test, g_seq_test = armijo_poincare(x_0_test, x_set_test, 0.2, 0.001, 0.25, 100)
print("Limit sequence poincare: ", psi_seq_test[-1])
plot_seq(x_set_test, psi_seq_test, f_seq_test, g_seq_test, limit_test, dim)

psi_seq_test, f_seq_test, g_seq_test = armijo_hyperboloid(x_0_test, x_set_test, 0.2, 0.0001, 0.25, 100)
print("Limit sequence iperboloide: ", psi_seq_test[-1])
plot_seq(x_set_test, psi_seq_test, f_seq_test, g_seq_test, limit_test, dim)

psi_seq_test, f_seq_test, g_seq_test = RBB_poincare(x_0_test, x_set_test, 0.0001, 0.9, 100)
print("Limit sequence poincare: ", psi_seq_test[-1])
plot_seq(x_set_test, psi_seq_test, f_seq_test, g_seq_test, limit_test, dim)

psi_seq_test, f_seq_test, g_seq_test = RBB_hyperboloid(x_0_test, x_set_test, 0.0001, 0.9, 100)
print("Limit sequence iperboloide: ", psi_seq_test[-1])
plot_seq(x_set_test, psi_seq_test, f_seq_test, g_seq_test, limit_test, dim)

sequence_fixed_lenght_poincare, sequence_fixed_lenght_hyper = test_one_parameter_optimization(
    optimisation_fl_poincare,
    optimisation_fl_hyperboloid,
    bunch[:20],
    100)

print(min(sequence_fixed_lenght_poincare))
alpha_D = (np.argmin(sequence_fixed_lenght_poincare)+1)/100
print(alpha_D)

plt.figure(figsize=(10,10))
plt.plot([i/100 for i in range(1, 100)], sequence_fixed_lenght_poincare)
plt.xlabel("parameter value", fontsize=18)
plt.ylabel("step to convergence", fontsize=18)
plt.savefig("fixed_step_parameter_poincare")

print(min(sequence_fixed_lenght_hyper))
alpha_H = (np.argmin(sequence_fixed_lenght_hyper)+1)/100
print(alpha_H)

plt.figure(figsize=(10,10))
plt.plot([i/100 for i in range(1, 100)], sequence_fixed_lenght_hyper)
plt.xlabel("parameter value", fontsize=18)
plt.ylabel("step to convergence", fontsize=18)
plt.savefig("fixed_step_parameter_hyperboloid")

sequence_armijo_poincare, sequence_armijo_hyper = test_one_parameter_optimization(
    lambda X0, X, learning_rate, max_iter: armijo_poincare(X0, X, 0.2, 0.001, learning_rate, max_iter),
    lambda X0, X, learning_rate, max_iter: armijo_hyperboloid(X0, X, 0.2, 0.001, learning_rate, max_iter),
    bunch[:10],
    100)

print(min(sequence_armijo_poincare))
lambda_D = (np.argmin(sequence_armijo_poincare)+1)/100
print(lambda_D)

plt.figure(figsize=(10,10))
plt.plot([i/100 for i in range(1, 100)], sequence_armijo_poincare)
plt.xlabel("parameter value", fontsize=18)
plt.ylabel("step to convergence", fontsize=18)
plt.savefig("armijo_parameter_poincare")

print(min(sequence_armijo_hyper))
lambda_H = (np.argmin(sequence_armijo_hyper)+1)/100
print(lambda_H)

plt.figure(figsize=(10,10))
plt.plot([i/100 for i in range(1, 100)], sequence_armijo_hyper)
plt.xlabel("parameter value", fontsize=18)
plt.ylabel("step to convergence", fontsize=18)
plt.savefig("armijo_parameter_hyperboloid")

test_algorithm(lambda X0, X, max_iter: optimisation_fl_poincare(X0, X, alpha_D, max_iter),
               lambda X0, X, max_iter: optimisation_fl_hyperboloid(X0, X, alpha_H, max_iter),
               bunch,
               100,
               "fixed_step_size",
               5)

test_algorithm(lambda X0, X, max_iter: armijo_poincare(X0, X, 0.2, 0.001, lambda_D, max_iter),
               lambda X0, X, max_iter: armijo_hyperboloid(X0, X, 0.2, 0.001, lambda_H, max_iter),
               bunch,
               100,
               "armijo",
               5)

test_algorithm(lambda X0, X, max_iter: RBB_poincare(X0, X, 0.0001, 0.9, max_iter),
               lambda X0, X, max_iter: RBB_hyperboloid(X0, X, 0.0001, 0.9, max_iter),
               bunch,
               100,
               "barzilai_borwein",
               5)