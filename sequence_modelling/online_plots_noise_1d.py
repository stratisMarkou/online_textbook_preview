import numpy as np
import matplotlib.pyplot as plt
from helper_functions import *
import matplotlib
import os
import matplotlib.gridspec as gridspec

def sample_lds(seq_length, A, C, Q, R, mu_0, V_0):

    xs = [np.random.multivariate_normal(mu_0, V_0)]
    ys = [np.random.multivariate_normal(C.dot(xs[-1]), R)]
    
    for i in range(seq_length):
        xs.append(np.random.multivariate_normal(A.dot(xs[-1]), Q))
        ys.append(np.random.multivariate_normal(C.dot(xs[-1]), R))
        
    return xs, ys

def kalman_gain(V, C, R):
    inverse_term = np.linalg.inv(C.dot(V).dot(C.T) + R)

    return V.dot(C.T).dot(inverse_term)

def kalman_filter(y, A, Q, C, R, mu_0, V_0):

    mean_post, cov_post = [mu_0], [V_0]
    mean_pred, cov_pred = [], []

    for i in range(len(y)):

        mean_pred.append(A.dot(mean_post[-1]))
        cov_pred.append(A.dot(cov_post[-1]).dot(A.T) + Q)

        K = kalman_gain(cov_pred[-1], C, R)
        mean_post.append(mean_pred[-1] + K.dot(y[i] - C.dot(mean_pred[-1])))
        cov_post.append(cov_pred[-1] - K.dot(C).dot(cov_pred[-1]))
        
    mean_pred.append(A.dot(mean_post[-1]))
    cov_pred.append(A.dot(cov_post[-1]).dot(A.T) + Q)

    return np.array(mean_post), np.array(cov_post), np.array(mean_pred), np.array(cov_pred)

matplotlib.rcParams['mathtext.fontset'] = 'stix'
matplotlib.rcParams['font.family'] = 'Georgia'

matplotlib.rc('axes', titlesize = 16)
matplotlib.rc('axes', labelsize = 16)
matplotlib.rc('xtick', labelsize = 12)
matplotlib.rc('ytick', labelsize = 12)

np.random.seed(0)

mean_0, cov_0 = np.array([0]), np.array([[1]]) # initial latent state parameters
lamda = 0.7

A_ = np.array([[lamda]])
Q_ = np.array([[1 - lamda**2]])
C_ = np.array([[1]])
R_ = 0.1*np.eye(1)
no_points = 200

xs, ys = sample_lds(no_points, A_, C_, Q_, R_, mean_0, cov_0)

result = kalman_filter(ys, A_, Q_, C_, R_, mean_0, cov_0)
mean_post, cov_post, mean_pred, cov_pred = result

mean = C_.dot(mean_pred.T).T[:, 0]
std = (C_.dot(cov_pred).dot(C_.T) + R_)[0, :, 0]**0.5
x_lim, y_lim = [-1, 21], [-4, 4]

x_low, x_high, no_grid = -4, 4, 500
grid = np.linspace(x_low, x_high, no_grid).reshape((no_grid, 1))
dx = (x_high - x_low)/no_grid

os.chdir('online_plots/noise_1d')
for i in range(20):
    
    fig = plt.figure(figsize = (12, 8))
    gs = gridspec.GridSpec(nrows=2, ncols=4, height_ratios=[1.3, 1])

    fig.add_subplot(gs[0, 1:3])
    beautify_plot({"title":"\nData space", "x":"Step number $t$", "y":"$y_t$"})
    
    plt.scatter(np.arange(0, i+1), ys[:i+1], marker = 'x', color = 'red',
                     zorder  = 2)

    if i > 0:
        plt.errorbar(i, mean[i], xerr = 0, yerr = std[i], color = 'black',
                     zorder = 1, capsize = 2)
    
    plt.xlim(x_lim), plt.ylim(y_lim)
    plt.xticks(np.linspace(0, 20, 6))

    fig.add_subplot(gs[1, 0])
    log_prior = -1/2*np.sum((grid - mean_post[i]).dot(np.linalg.inv(cov_post[i]))*(grid - mean_post[i]),
                             axis = -1)
    prior = np.exp(log_prior)/np.exp(log_prior).sum()/dx
    plt.plot(grid, prior, color = 'black')

    title = "Prior (t = {})\n".format(i) + "$p(\mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"})
    plt.ylim([-0.1, 1.8])
    plt.yticks([0, 0.5, 1, 1.5])


    fig.add_subplot(gs[1, 1])
    log_lik = -1/2*np.sum((ys[i] - grid.dot(C_.T)).dot(np.linalg.inv(R_))*(ys[i] - grid.dot(C_.T)),
                          axis = -1)
    lik = np.exp(log_lik)/np.exp(log_lik).sum()/dx
    plt.plot(grid, lik, color = 'black')

    title = "Likelihood (t = " + str(i) +")\n$p(\mathbf{y}_t| \mathbf{x}_t)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{y}_t| \mathbf{x}_t)$"})
    plt.ylim([-0.1, 1.8])

    fig.add_subplot(gs[1, 2])
    plt.plot(grid, lik*prior, color = 'black')

    title = "Posterior (t = "+str(i)+")\n$p(\mathbf{y}_t, \mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{y}_t, \mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"})
    plt.ylim([-0.1, 1.8])

    fig.add_subplot(gs[1, 3])
    log_post_ = -1/2*np.sum((mean_post[i+1] - grid).dot(np.linalg.inv(cov_post[i+1]))*(mean_post[i+1] - grid),
                            axis = -1)
    plt.plot(grid, np.exp(log_post_)/np.exp(log_post_).sum()/dx, color = 'black')


    title = "Pred. posterior (t ="+str(i)+")\n$p(\mathbf{x}_{t+1} | \mathbf{y}_t, ... , \mathbf{y}_0)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{x}_{t+1} | \mathbf{y}_t, ... , \mathbf{y}_0)$"})
    plt.ylim([-0.1, 1.8])
    
    plt.tight_layout(w_pad = 0)
    
    plt.savefig(str(2*i).zfill(3) + '.png', dpi = 400)
    plt.close()

    

    
    fig = plt.figure(figsize = (12, 8))
    gs = gridspec.GridSpec(nrows=2, ncols=4, height_ratios=[1.3, 1])

    fig.add_subplot(gs[0, 1:3])
    plt.scatter(np.arange(0, i + 1), ys[:i+1], marker = 'x', color = 'red',
                     zorder = 2)

    plt.errorbar(i+1, mean[i+1], xerr = 0, yerr = std[i+1], color = 'black',
                     zorder = 1, capsize = 2)
    
    plt.xlim(x_lim), plt.ylim(y_lim)
    plt.xticks(np.linspace(0, 20, 6))
    beautify_plot({"title":"\nData space", "x":"Step number $t$", "y":"$y_t$"})


    fig.add_subplot(gs[1, 0])
    log_prior = -1/2*np.sum((grid - mean_post[i]).dot(np.linalg.inv(cov_post[i]))*(grid - mean_post[i]),
                             axis = -1)
    prior = np.exp(log_prior)/np.exp(log_prior).sum()/dx
    plt.plot(grid, prior, color = 'black')

    title = "Prior (t = {})\n".format(i) + "$p(\mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"})
    plt.ylim([-0.1, 1.8])
    plt.yticks([0, 0.5, 1, 1.5])


    fig.add_subplot(gs[1, 1])
    log_lik = -1/2*np.sum((ys[i] - grid.dot(C_.T)).dot(np.linalg.inv(R_))*(ys[i] - grid.dot(C_.T)),
                          axis = -1)
    lik = np.exp(log_lik)/np.exp(log_lik).sum()/dx
    plt.plot(grid, lik, color = 'black')

    title = "Likelihood (t = " + str(i) +")\n$p(\mathbf{y}_t| \mathbf{x}_t)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{y}_t| \mathbf{x}_t)$"})
    plt.ylim([-0.1, 1.8])

    fig.add_subplot(gs[1, 2])
    plt.plot(grid, lik*prior, color = 'black')

    title = "Posterior (t = "+str(i)+")\n$p(\mathbf{y}_t, \mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{y}_t, \mathbf{x}_t| \mathbf{y}_{t-1},...,\mathbf{y}_0)$"})
    plt.ylim([-0.1, 1.8])

    fig.add_subplot(gs[1, 3])
    log_post_ = -1/2*np.sum((mean_post[i+1] - grid).dot(np.linalg.inv(cov_post[i+1]))*(mean_post[i+1] - grid),
                            axis = -1)
    plt.plot(grid, np.exp(log_post_)/np.exp(log_post_).sum()/dx, color = 'black')


    title = "Pred. posterior (t ="+str(i)+")\n$p(\mathbf{x}_{t+1} | \mathbf{y}_t, ... , \mathbf{y}_0)$"
    beautify_plot({"title":title, "x":"$x$", "y":"$p(\mathbf{x}_{t+1} | \mathbf{y}_t, ... , \mathbf{y}_0)$"})
    plt.ylim([-0.1, 1.8])
    
    plt.tight_layout(w_pad = 0)
    
    plt.savefig(str(2*i + 1).zfill(3) + '.png', dpi = 400)
    plt.close()
