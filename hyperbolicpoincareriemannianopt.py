# -*- coding: utf-8 -*-
"""HyperbolicPoincareRiemannianOpt.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/132nPifYdtpjx8cs9N-e0fpdEZJqGGC9Q

# riferimenti
- https://juliamanifolds.github.io/Manifolds.jl/stable/manifolds/hyperbolic.html
- https://geoopt.readthedocs.io/en/poincare/extended/poincare.html
- https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7108814/
- http://proceedings.mlr.press/v119/bose20a/bose20a.pdf
"""

import numpy as np
from random import random
import math
import matplotlib.pyplot as plt
from numpy import linalg as LA
import numpy.linalg as la
from mpmath import mp, mpf, acosh
!pip install pymanopt
import pymanopt
from pymanopt.manifolds.manifold import Manifold
mp.dps = 32

import inspect
print(inspect.getsource(Manifold))

"""# Poincare Ball

"""

class PoincareBall(Manifold):
  def __init__(self, dimension):
    # super().__init__("PoincareBall", dimension) # la versione nel pypi è una versione vecchia della superclasse Manifold
    self._name = f"PoincareBall over R^{dimension}"
    self._dimension = dimension

  # ----------
  def __str__(self):
    """
    Name of the manifold
    """
    return self._name

  @property
  def dim(self):
    """
    Dimension of the manifold
    """
    return self._dimension
  # ----------

  def conformal_factor(self, x):
    return 2/(1 - np.dot(x, x))
  
  def mobius_add(self, x, y):
    x_dot_y = np.dot(x, y)
    x_norm_q = np.dot(x, x)
    y_norm_q = np.dot(y, y)

    num = (1 + 2*x_dot_y + y_norm_q)*x + (1 - x_norm_q)*y
    den = 1 + 2*x_dot_y + x_norm_q*y_norm_q

    if den == 0:
      den = 10e-14

    return num/den

  def typicaldist(self):
    return self.dim / 8
  
  def inner(self, X, G, H):
    return self.conformal_factor(X)**2*np.dot(G,H)

  def proj(self, X, G):
    # Identity map since the embedding space is the tangent space R^n
    return G
  
  def norm(self, X, G):
    return self.conformal_factor(X)*la.norm(G)

  def rand(self):
    passisotropic = np.random.rand(self.dim)
    isotropic = isotropic / la.norm(isotropic);
    radius = random ** (1 / self.dim);
    x = isotropic * radius
    return x

  def randvec(self, X):
    v = np.random.rand(self.dim)
    v = v / self.norm(X, v);
    return v

  def zerovec(self, X):
    return np.zeros(X.shape)

  def dist(self, X, Y):
    a = max(1, 1 + 2*(np.dot(X-Y, X-Y)/((1-np.dot(X,X))*(1-np.dot(Y,Y)))))
    return np.arccosh(a)
  
  def egrad2rgrad(self, X, G):
    factor_q = self.conformal_factor(X)**2
    return G/factor_q
  
  def ehess2rhess(self, X, G, H, U):
    factor = self.conformal_factor(X)
    return (U * np.dot(G, X) - G * np.dot(U, X) - X * np.dot(U, G) + H/factor)/factor

  def retr(self, X, U):
    return self.exp(X, U)

  def exp(self, X, U):
    norm_u = la.norm(U)
    # avoid division by 0
    tmp = np.tanh(1/2*self.norm(X, U))*(U/((norm_u + (norm_u==0))))
    return self.mobius_add(X, tmp)

  def log(self, X, Y):
    a = self.mobius_add(-X, Y)
    b = math.sqrt(np.dot(a, a))
    c = 2/self.conformal_factor(X)*np.arctanh(b)
    return c*a/b

  def transp(self, X1, X2, G):
    return G
  
  def pairmean(self, X, Y):
    return self.exp(X, self.log(X, Y) / 2);

"""# Hyperboloid"""

class Hyperboloid(Manifold):
  def __init__(self, dimension):
    # super().__init__(self, "Hyperboloid", dimension)
    self._name = f"Hyperboloid over R^{dimension+1}"
    self._dimension = dimension

  # ----------
  def __str__(self):
    """
    Name of the manifold
    """
    return self._name

  @property
  def dim(self):
    """
    Dimension of the manifold
    """
    return self._dimension
  # ----------

  def _minkowski_dot(self, X, Y):
    return np.dot(X[:-1], Y[:-1]) - X[-1]*Y[-1]

  def typicaldist(self):
    return math.sqrt(self.dim)
  
  def inner(self, X, G, H):
    return self._minkowski_dot(G, H)

  def proj(self, X, G):
    inner = self._minkowski_dot(X, G);
    return G + X*inner;
  
  def norm(self, X, G):
    return math.sqrt(max(0, self._minkowski_dot(G, G)))

  def rand(self):
    ret = np.zeros(self.dim+1)
    x0 = np.random.normal(self.dim)
    x1 = sqrt(1 + np.dot(x0))
    ret[:-1] = x0
    ret[-1] = x1
    return ret

  def randvec(self, X):
    U = self.proj(X, np.random.rand(X.shape))
    return U / self.norm(X, U)

  def zerovec(self, X):
    return np.zeros(X.shape)

  def dist(self, X, Y):
    alpha = max(1, -minkowski_dot(X, Y))
    return np.arccosh(alpha)

  def egrad2rgrad(self, X, G):
    G[-1] = -G[-1]
    return projection(X, G)

  def ehess2rhess(self, X, G, H, U):
    G[-1] = -G[-1]
    H[:, -1] = -H[:, -1] # TODO da rivedere come viene trattata la matrice hessiana
    inners = self._minkowski_dot(X, G)
    return self.proj(X, U*inners + H);

  def retr(self, X, U):
    self.exp(X, U)

  def exp(self, X, U):
    mink_norm_u = self.norm(X, U)
    a = np.sinh(mink_norm_u)/mink_norm_u
    if mink_norm_u == 0:
      a = 1
    return np.cosh(mink_norm_u)*X + U*a

  def log(self, X, Y):
    alpha = max(1, -self._minkowski_dot(X, Y))
    if alpha == 1:
      a = 1
    else:
      a = np.arccosh(alpha)/((alpha**2 - 1)**(1/2))
    return (a)*(Y - alpha*X)

  def transp(self, X1, X2, G):
    return self.proj(X2, G);
  
  def pairmean(self, X, Y):
    return self.exp(X, self.log(X, Y), 1/2)

"""### Derivate of the loss Function"""

# --- Poincare Gradiend
def poincare_dist_grad(x, y):
  a = 1 - np.dot(x, x)
  b = 1 - np.dot(y, y)
  c = 1 + 2/(a*b)*(np.dot(x-y, x-y))
  
  return 4/(b*math.sqrt(c**2-1))*(((np.dot(y,y) - 2*np.dot(x, y) + 1)/a**2)*x - y/a)


def frechet_mean_poincare_grad(psi, x_set):
  res = 0
  for x_i in x_set:
    res += poincare_dist(psi, x_i)*grad_poincare_dist(psi, x_i)
  return res*2*(len(x_set))

def frechet_mean_poincare_rgrad(psi, x_set):
  egrad = frechet_mean_poincare_grad(psi, x_set)
  factor_q = lambda_x(psi)**2
  return egrad/factor_q

# --- Hyperboloid Gradient
def frechet_mean_hyperboloid_grad(theta, x_set):
  res = 0
  for x_i in x_set:
    x_i_g = x_i.copy()
    x_i_g[-1] = -x_i_g[-1]
    res += -(hyperboloid_dist(theta, x_i) * (minkowski_dot(theta, x_i)**2 - 1)**(-1/2)) * x_i_g
  res = res*2/(len(x_set))
  return res

def frechet_mean_hyperboloid_rgrad(theta, x_set):
  egrad = frechet_mean_hyperboloid_grad(theta, x_set)
  egrad[-1] = -egrad[-1]
  return hyperboloic_projection(theta, egrad)

def frechet_mean(theta, x_set, distance):
  sum_ = 0
  s = len(x_set)
  for x_i in x_set:
    sum_ += distance(theta, x_i)**2
  return sum_/s

def poincare_points_factory(norm=1):
  # non è uniforme nel disco di poincaré, ma è piu vicino al centro
  z = random()
  t = random()*2*math.pi
  return np.array([z*np.cos(t), z*np.sin(t)])


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


def poincare_dist_mpf(x, y):
  return acosh(1 + 2*(np.dot(x-y, x-y)/((1-np.dot(x,x))*(1-np.dot(y,y)))))


def convergence_seq(psi_seq, limit):
  return [poincare_dist_mpf(psi, limit) for psi in psi_seq]
  # return [LA.norm(psi - limit) for psi in psi_seq] # euclidean norm


# TODO: sostituire norma euclidea con variabile a seconda del metodo del calcolo
# del gradiente
def plot_seq(psi_seq, f_seq, g_seq, limit, dimm):
  fig = plt.figure(figsize=[12.8, 12.8])
  fig.clf()
  gs = fig.add_gridspec(2, 2)
  ax1 = fig.add_subplot(gs[0, 0])
  ax1.title.set_text("poincaré ball over complexes (R^2)")
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
  g_norm = [LA.norm(g) for g in g_seq]
  ax4.semilogy((g_norm))

"""# Verifica Sperimentale Mappa Conforme"""

x = np.array([2.9759471, 16.07711731, 16.38078027])#inv_rho(poincare_points_factory())

print(x)

a_set_1 = [inv_rho(poincare_points_factory()), inv_rho(poincare_points_factory())]
a_set_2 = [inv_rho(poincare_points_factory()), inv_rho(poincare_points_factory())]
v = hyperboloid_gradient(x, a_set_1)
w = hyperboloid_gradient(x, a_set_2)

print(v)
print(w)


def differential_map(x, v):
  n = x.shape[0]-1
  delta_f_v = np.zeros(n)
  for i in range(n):
    delta_f_v[i] = (v[i] - (x[i]*v[-1])/(x[-1] + 1))
  return delta_f_v

  
delta_f_v = differential_map(x, v)
print(delta_f_v)
delta_f_w = differential_map(x, w)
print(delta_f_w)
r = lambda_x(x)**2 * np.dot(delta_f_v, delta_f_w)

s = minkowski_dot(v, w)

print((s/r))

"""# Cariamento dei dati"""

def generate_starting_point(x_set):
  psi_0 = np.zeros(x_set.shape[1]) # poincare_points_factory() # calcolare come media dei punti x_set
  for a_i in x_set:
    psi_0 += a_i
  psi_0 /= len(x_set)
  return psi_0

def generate_sets_from_file(file_name="points.txt"):
  x_set_s = []
  with open(file_name, "r") as f:
    for line in f.readlines():
      line_els = line.split(",")
      dim = int(line_els[0])
      limit = [mpf(i) for i in line_els[-dim:]]
      x_set = []
      for i in range(1, len(line_els)-dim, dim):
        x_set.append([float(i) for i in line_els[i:i+dim]])
      x_set = np.array(x_set)
      x_set_s.append((dim, x_set, limit))
  return x_set_s

x_set_s = generate_sets_from_file()

print(x_set_s)

dim, x_set, limit = x_set_s[1]

print(dim)
print(x_set)
print(limit)

PoincareManifold = PoincareBall(dim)
HyperboloidManifold = Hyperboloid(dim)

"""# Metodo iterativo

parte da un punto a_i e si va nella direzione del secondo seguendo la geodedica e ci si ferma ad 1/2 poi si va verso il terzo punto e si prosegue per 1/3 poi si va verso il quarto putno e si prosegue per 1/4 e cosi via. x_k+1 = exp(log(x_k, a_(k%p)), 1/k); p = # punti.  
converge al baricentro
"""

def iterative_method(manifold, x_set, max_steps=10):
  m = len(x_set)
  x_k = x_set[0]
  for i in range(1, max_steps):
    j = (i)%m
    a_j = x_set[j]
    x_k = manifold.exp(x_k, manifold.log(x_k, a_j)/(i+1))
  return x_k

def iterative_method_poincare(x_set, max_steps=10):
  m = len(x_set)
  x_k = x_set[0]
  for i in range(1, max_steps):
    j = (i)%m
    a_j = x_set[j]
    x_k = poincare_exp(x_k, poincare_log(x_k, a_j)/(i+1))
  return x_k

def iterative_method_hyperboloid(x_set, max_steps=10):
  m = len(x_set)
  x_k = x_set[0]
  for i in range(1, max_steps):
    j = (i)%m
    a_j = x_set[j]
    x_k = hyperboloid_exp(x_k, hyperboloid_log(x_k, a_j)/(i+1))
  return x_k

limit_iter = iterative_method(PoincareManifold, x_set, 100000)
print(limit_iter)

limit_iter = rho(iterative_method(HyperboloidManifold, [inv_rho(x) for x in x_set], 100000))
print(limit_iter)

limit_iter = iterative_method_poincare(x_set, 100000)
print(limit_iter)

limit_iter = rho(iterative_method_hyperboloid([inv_rho(x) for x in x_set], 100000))
print(limit_iter)

"""# Scelta del punto iniziale"""

# scelta del passo inizale come iterata i-esima dell'algoritmo iterativo che sappiamo convergere, perciò aumentando i avremo psi_0 sempre più vicino al nostro punto limite
psi_0 = iterative_method_poincare(x_set, 10)
print(psi_0)

#
#psi_0 = generate_starting_point(x_set)

"""# Optimisations Algorithms


"""

def C_complex(z): # trasformata di Cayley
  return (1-z)/(1+z)


def C(a): # wrapper trasformata di Cayley
  z = np.complex(a[0], a[1])
  ret = C_complex(z)
  return np.array([ret.real, ret.imag])


def direct_g(a_set):
  return C_complex(np.prod([C_complex(np.complex(a[0], a[1])) for a in a_set])**(1/len(a_set)))


direct_g(x_set)

"""## Algoritmo Per il baricentro di riferimento"""

from math import exp

# IANNAZZO IMPLEMENTATION
def poincare_points_factory_complex(norm=1):
  # non è uniforme nel disco di poincaré, ma è piu vicino al centro
  z = random()
  t = random()*2*math.pi
  return np.complex(z*np.cos(t),z*np.sin(t))


def complex_sign(z: complex) -> complex:
  if z==0:
    return 1
  return z/np.absolute(z)


def poincare_tangent_complex(a: complex, b: complex) -> complex:
  s = (b-a)/(1-a.conjugate()*b)
  v = complex_sign(s) *(1-np.absolute(a)**2)
  v = v*np.arctanh(np.absolute(s))
  return v


def poincare_geodesic_complex(x: complex, v: complex, t: float) -> complex:
  tmp = 2*np.absolute(v)/(1-np.absolute(x)**2)
  num = (x+(complex_sign(v)))+(x-(complex_sign(v)))*exp(-tmp*t)
  den = (1+x.conjugate()*(complex_sign(v)))+(1-x.conjugate()*(complex_sign(v)))*exp(-tmp*t)
  return num/den


def r2_to_complex_array(points):
  return [np.complex(a[0], a[1]) for a in points]

def complex_to_r2_array(points):
  return [np.array([z.real, z.imag]) for z in points]

# implemento algoritmi del professor iannazzo come riferimento per il calcolo
# del baricentro
def poincare_barycenter_iannazzo(data, par, maxit=100):
  x0 = 0
  psi_seq = [x0]
  m = len(data)
  for k in range(m):
    x0=x0+data[k]/m

  for h in range(maxit):
    incr=0
    for k in range(m):
      ai=data[k]
      incr=incr+poincare_tangent_complex(x0,ai)
    x1=poincare_geodesic_complex(x0, incr, par)
    if np.absolute(x1-x0)<10e-15:
      break
    psi_seq.append(x0)
    x0=x1
  return psi_seq


def plot_psi_seq(psi_seq, limit, dim):
  fig = plt.figure(figsize=[6.4, 12.8])
  fig.clf()
  gs = fig.add_gridspec(2, 1)
  ax1 = fig.add_subplot(gs[0, 0])
  ax1.title.set_text("poincaré ball over complexes (R^2)")
  ax2 = fig.add_subplot(gs[1, 0])
  ax2.title.set_text("error sequence")

  if dim == 2:
    plot_alg(psi_seq, x_set, ax1)
  conv_seq = convergence_seq(psi_seq, limit)
  ax2.semilogy(conv_seq)

print(limit)

if dim == 2:
  x_set_complex = r2_to_complex_array(x_set)
  seq = poincare_barycenter_iannazzo(x_set_complex, 0.1, 1000)
  seq = complex_to_r2_array(seq)
  print("Limit sequence poincare: ", seq[-1])
  plot_psi_seq(seq, limit, dim)

"""## Fixed Length step size"""

def optimisation_fl_poincare(psi_0, f_grad, learning_rate, x_set, max_steps=10):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []

  for i in range(max_steps):
    psi = psi_seq[-1]
    g = f_grad(psi, x_set)
    if np.isnan(g).any():
      psi_seq = psi_seq[:-1]
      break
    if (g==0).any():
      break
    new_psi=PoincareManifold.exp(psi, -learning_rate*g)

    if math.sqrt(np.dot(new_psi, new_psi)) >= 1:
      break
    
    psi_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, PoincareManifold.dist))
    g_seq.append(g)
  return psi_seq, f_seq, g_seq


def optimisation_fl_hyperboloid(psi_0, f_grad, learning_rate, x_set, max_steps=10):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []
  x_set_h = [inv_rho(x_i) for x_i in x_set]

  for i in range(max_steps):
    psi = psi_seq[-1]
    theta=inv_rho(psi)
    g_h = f_grad(theta, x_set_h)
    if np.isnan(g_h).any():
      psi_seq = psi_seq[:-1]
      break
    if (g_h==0).any():
      break
    new_theta = HyperboloidManifold.exp(theta, -learning_rate*g_h)
    new_psi = rho(new_theta)
    
    psi_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, PoincareManifold.dist))
    g_seq.append(g_h)
  return psi_seq, f_seq, g_seq

psi_seq, f_seq, g_seq = optimisation_fl_poincare(psi_0, frechet_mean_poincare_rgrad, 0.31, x_set, 100)
print("Limit sequence poincare: ", psi_seq[-1])
print(psi_seq)
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

psi_seq, f_seq, g_seq = optimisation_fl_poincare(psi_0, frechet_mean_poincare_grad, 0.002, x_set, 100)
print("Limit sequence poincare euclideo: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

psi_seq, f_seq, g_seq = optimisation_fl_hyperboloid(psi_0, frechet_mean_hyperboloid_rgrad, 0.45, x_set, 100)
print("Limit sequence iperboloide: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

"""### Armijo"""

def armijo_step_hiper_riemannian(theta, x_set_h, g_k, sigma, gamma, lambda_):
  h = 0
  while frechet_mean(HyperboloidManifold.exp(theta, -(sigma**h)*lambda_*g_k), x_set_h, HyperboloidManifold.dist) > frechet_mean(theta, x_set_h, HyperboloidManifold.dist) - gamma*(sigma**h)*lambda_*HyperboloidManifold._minkowski_dot(g_k, g_k):
    h += 1
  return h

def armijo_opt_hiper_riemannian(psi_0, f_grad, x_set, sigma, gamma, lambda_, max_iter=10):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []
  x_set_h = [inv_rho(x) for x in x_set]

  for k in range(max_iter):
    theta = inv_rho(psi_seq[-1])
    g_k = f_grad(theta, x_set_h)
    if np.isnan(g_k).any():
      psi_seq = psi_seq[:-1]
      break
    if (g_k==0).any():
      break
    h_k = armijo_step_hiper_riemannian(theta, x_set_h, g_k, sigma, gamma, lambda_)
    new_theta = HyperboloidManifold.exp(theta, -(sigma**h_k)*lambda_*g_k)
    new_psi = rho(new_theta)
    
    psi_seq.append(rho(new_theta))
    f_seq.append(frechet_mean(new_psi, x_set, poincare_dist))
    g_seq.append(g_k)
  return psi_seq, f_seq, g_seq

def armijo_step_poincare_riemannian(psi, x_set, g_k, sigma, gamma, lambda_):
  h = 0
  while frechet_mean(PoincareManifold.exp(psi, -(sigma**h)*lambda_*g_k), x_set, PoincareManifold.dist) > frechet_mean(psi, x_set, PoincareManifold.dist) + gamma*(sigma**h)*lambda_*(PoincareManifold.conformal_factor(psi)**2*np.dot(g_k, -g_k)):
    h += 1
  return h

def armijo_opt_poincare_riemannian(psi_0, f_grad, x_set, sigma, gamma, lambda_, max_iter=10):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []

  for k in range(max_iter):
    psi = psi_seq[-1]
    g_k = f_grad(psi, x_set)
    if np.isnan(g_k).any():
      psi_seq = psi_seq[:-1]
      break
    if (g_k==0).any():
      break
    h_k = armijo_step_poincare_riemannian(psi, x_set, g_k, sigma, gamma, lambda_)
    new_psi = PoincareManifold.exp(psi, -(sigma**h_k)*lambda_*g_k)
    
    psi_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, poincare_dist))
    g_seq.append(g_k)
  return psi_seq, f_seq, g_seq

psi_seq, f_seq, g_seq = armijo_opt_poincare_riemannian(psi_0, frechet_mean_poincare_grad, x_set, 0.3, 0.001, 0.9, 100)
print("Limit sequence poincare euclidean: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

psi_seq, f_seq, g_seq = armijo_opt_poincare_riemannian(psi_0, frechet_mean_poincare_rgrad, x_set, 0.3, 0.001, 0.9, 100)
print("Limit sequence poincare: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

psi_seq, f_seq, g_seq = armijo_opt_hiper_riemannian(psi_0, frechet_mean_hyperboloid_rgrad, x_set, 0.3, 0.1, 0.9, 100)
print("Limit sequence iperboloide: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

"""### Barzilai-Borwein"""

def RBB_hyperboloid(psi_0, f_grad, x_set, a_min, a_max, max_steps=10):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []

  x_set_h = [inv_rho(x_i) for x_i in x_set]
  theta_0 = inv_rho(psi_0)

  f_k_seq = []

  a_BB = a_min
  for k in range(max_steps):
    theta = inv_rho(psi_seq[-1])
    g_k = f_grad(theta, x_set_h)
    f_k_seq.append(frechet_mean(theta, x_set_h, HyperboloidManifold.dist))
    a_k = a_BB
    new_theta = HyperboloidManifold.exp(theta, -a_k*g_k)
    new_psi = rho(new_theta)
    
    psi_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, poincare_dist))
    g_seq.append(g_k)

    new_f = frechet_mean(new_theta, x_set_h, HyperboloidManifold.dist)
    new_g = f_grad(new_theta, x_set_h)
    s_k = -a_k*HyperboloidManifold.transp(theta, new_theta, g_k)
    y_k = new_g + s_k/a_k

    if minkowski_dot(s_k, y_k) > 0:
      new_tau = HyperboloidManifold._minkowski_dot(s_k, s_k)/HyperboloidManifold._minkowski_dot(s_k, y_k)
      a_BB = min(a_max, max(a_min, new_tau))
    else:
      a_BB = a_max
      
  return psi_seq, f_seq, g_seq

def RBB_poincare(psi_0, f_grad, x_set, a_min, a_max, max_steps=10):
  psi_seq = [psi_0]
  f_seq = []
  g_seq = []

  f_k_seq = []

  a_BB = a_min
  for k in range(max_steps):
    psi = psi_seq[-1]
    g_k = f_grad(psi, x_set)
    f_k_seq.append(frechet_mean(psi, x_set, PoincareManifold.dist))
    a_k = a_BB
    new_psi = PoincareManifold.exp(psi, -a_k*g_k)
    
    psi_seq.append(new_psi)
    f_seq.append(frechet_mean(new_psi, x_set, PoincareManifold.dist))
    g_seq.append(g_k)

    new_f = frechet_mean(new_psi, x_set, PoincareManifold.dist)
    new_g = f_grad(new_psi, x_set)
    s_k = -a_k*PoincareManifold.transp(psi, new_psi, g_k)
    y_k = new_g + s_k/a_k

    if PoincareManifold.conformal_factor(new_psi)**2*np.dot(s_k, y_k) > 0:
      new_tau = PoincareManifold.conformal_factor(new_psi)**2*np.dot(s_k, s_k)/(PoincareManifold.conformal_factor(new_psi)**2*np.dot(s_k, y_k))
      a_BB = min(a_max, max(a_min, new_tau))
    else:
      a_BB = a_max
  return psi_seq, f_seq, g_seq

psi_seq, f_seq, g_seq = RBB_poincare(psi_0, frechet_mean_poincare_grad, x_set, 0.0001, 0.9, 100)
print("Limit sequence poincare euclidean: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

psi_seq, f_seq, g_seq = RBB_poincare(psi_0, frechet_mean_poincare_rgrad, x_set, 0.0001, 0.9, 100)
print("Limit sequence poincare: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

# supporta un learnign rate piu alto convergendo in modo piu veloce
psi_seq, f_seq, g_seq = RBB_hyperboloid(psi_0, frechet_mean_hyperboloid_rgrad, x_set, 0.001, 0.9, 100)
print("Limit sequence iperboloide: ", psi_seq[-1])
plot_seq(psi_seq, f_seq, g_seq, limit, dim)

"""# Confronto tra le due metodologie

per ogni tipologia di algoritmo confrontiamo al variare dei parametri come variano e si comporta l'implementazione su iperboloide rispetto a quella su disco di Poincaré
"""

fixed_lenght_poincare = []
fixed_lenght_hyper = []

def differences(seq):
  differences = []
  for s in seq:
    s = s - limit
    differences.append(math.sqrt(np.dot(s, s)) < epsilon)
  return differences

epsilon = 10e-15
iter_ = 1000
for i in range(1, iter_):
  poincare_seq, _, _= optimisation_fl_poincare(psi_0, frechet_mean_poincare_rgrad, (i/iter_), x_set, 100)
  min_poincare = np.argmax(differences(poincare_seq))
  print(differences(poincare_seq))
  if min_poincare == 0:
    min_poincare = 100+1
  fixed_lenght_poincare.append(min_poincare)
  hyper_seq, _, _ = optimisation_fl_hyperboloid(psi_0, frechet_mean_hyperboloid_rgrad, (i/iter_), x_set, 100)
  min_hyper = np.argmax(differences(hyper_seq))
  if min_hyper == 0:
    min_hyper = 100+1
  fixed_lenght_hyper.append(min_hyper)

print(min(fixed_lenght_poincare))
plt.plot([i/iter_ for i in range(1, iter_)], fixed_lenght_poincare)

print(min(fixed_lenght_hyper))
plt.plot([i/iter_ for i in range(1, iter_)], fixed_lenght_hyper)