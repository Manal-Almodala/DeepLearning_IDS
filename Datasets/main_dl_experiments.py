import sys
import numpy as np
from sklearn import preprocessing
import SYS_VARS
import load_dataset as kdd
from autoencoders import SparseAutoencoder
from MLP_nets import MLP_general
import scipy.optimize
import analysis_functions


###########################################################################################

def normalize_dataset(dataset):
    """ Normalize the dataset provided as input, values in scalte 0 to 1 """
    min_max_scaler = preprocessing.MinMaxScaler()
    return min_max_scaler.fit_transform(dataset)

def sparse_normalize_dataset(dataset):
    """ Normaliza dataset without removing the sparseness structure of the data """
    #Remove mean of dataset 
    dataset = dataset - np.mean(dataset)
    #Truncate to +/-3 standard deviations and scale to -1 to 1
    std_dev = 3 * np.std(dataset)
    dataset = np.maximum(np.minimum(dataset, std_dev), -std_dev) / std_dev
    #Rescale from [-1, 1] to [0.1, 0.9]
    #dataset = (dataset + 1) * 0.4 + 0.1
    dataset = (dataset-np.amin(dataset))/(np.amax(dataset)-np.amin(dataset))
    return dataset
    #return preprocessing.MaxAbsScaler().fit_transform(dataset)



def softmax (x):
    """ Compute softmax values for each sets of scores in x.
        S(xi) =  exp[xi] / Sum {exp[xi]} 
    """
    assert len(x.shape) == 2
    s = np.max(x, axis=1)
    s = s[:, np.newaxis] # necessary step to do broadcasting
    e_x = np.exp(x - s)
    s_denom = np.sum(e_x, axis=1)
    s_denom = s_denom[:, np.newaxis] # dito
    return e_x / s_denom


###########################################################################################

def execute_sparseAutoencoder(rho, lamda, beta, max_iterations, visible_size, hidden_size, train_data):  
    """ Trains the Autoencoder with the trained data and parameters and returns train_data after the network """
    
    #Initialize the Autoencoder with its parameters and train
    encoder = SparseAutoencoder(visible_size, hidden_size, rho, lamda, beta)
    #opt_solution  = scipy.optimize.minimize(encoder, encoder.theta, args = (training_data,), method = 'L-BFGS-B', jac = True, options = {'maxiter': max_iterations, 'disp' : True})
    opt_solution = encoder.train (train_data, max_iterations)
    if (opt_solution.success):
        print (opt_solution.message)
        
    # Recover parameters from theta = (W1_grad.flatten(), W2_grad.flatten(), b1_grad.flatten(), b2_grad.flatten())
    opt_theta     = opt_solution.x
    opt_W1        = opt_theta[encoder.limit0 : encoder.limit1].reshape(hidden_size, visible_size)
    opt_W2        = opt_theta[encoder.limit1 : encoder.limit2].reshape(visible_size, hidden_size)
    opt_b1        = opt_theta[encoder.limit2 : encoder.limit3].reshape(hidden_size, 1)
    opt_b2        = opt_theta[encoder.limit3 : encoder.limit4].reshape(visible_size, 1)

    # Compute one data sample: input vs output
    """print("\nInput value ")
    x_in = training_data[:,4:5]
    #x_in= training_data.take([[:,5],[5]])
    print (x_in)
    opt_H, opt_X = encoder.compute_layer(x_in, opt_W1, opt_W2, opt_b1, opt_b2)"""
    
    """visualizeW1(opt_W1, vis_patch_side, hid_patch_side)"""
    """print("\nOutput value " )
    print (opt_X)"""

    # Return input dataset computed with autoencoder
    return encoder.compute_dataset(train_data, opt_W1, opt_W2, opt_b1, opt_b2)

def execute_MLP(train_data, hidden_layers, y, classes_names):
    """ Trains the MLP with the train_data and returns train_data after the network """
    # Train
    mlp = MLP_general(hidden_layers)    
    print ("Training..."+str(y.shape) +  "(labels) and " +str(train_data.shape)+"(dataset)")
    mlp.train(np.transpose(train_data), y, 'trial')
    print ("To test..."+str(train_data[kdd._ATTACK_INDEX_KDD, 4:5]))
    # Compute for all train_data
    """ Compute one sample - train_data[:, 4:5]
    prediction1 = mlp.test(np.transpose(train_data[:, 4:5]))
    print ("Prediction: " + str(prediction16))
    for value in prediction1:
        for k in kdd.attacks_map.keys():
            if (int(value) == kdd.attacks_map[k]):
                print(k)"""
    y_data = mlp.compute_dataset(train_data)
    #analysis_functions.print_totals(y_data, y)

    return mlp, y_data


########### IDS with DEEPLEARNING #############################

def ids_mlp(train_data, y, classes_names):
        
    ######## MULTILAYER PERCEPTRONS
    h_layers = [64]          # hidden layers, defined by their sizes {i.e 2 layers with 30 and 20 sizes [30, 20]}
    mlp, y_predicted = execute_MLP(train_data, hidden_layers = h_layers,y =  y, classes_names = classes_names)
    print(str(y_predicted[1]) +" vs real: "+ str(y[1]))

    return mlp, y_predicted
def deeplearning_sae_mlp(train_data, y, classes_names):

    ######## SPARSE AUTOENCODER TRAINING
    """ Define the parameters of the Autoencoder """
    rho            = 0.01   # desired average activation of hidden units... should be tuned!!
    lamda          = 0.0001 # weight decay parameter
    beta           = 3      # weight of sparsity penalty term
    max_iterations = 400    # number of optimization iterations
    visible_size = 41       # input & output sizes: KDDCup99 # of features
    hidden_size = 50        # sparse-autoencoder benefits from larger hidden layer units """
    """ Train and do a test over the same traindata """
    featured_x = execute_sparseAutoencoder(rho, lamda, beta, max_iterations, visible_size, hidden_size, train_data)
    
        
    ######## MULTILAYER PERCEPTRONS
    h_layers = [64]          # hidden layers, defined by their sizes {i.e 2 layers with 30 and 20 sizes [30, 20]}
    mlp, y_predicted = execute_MLP(featured_x, hidden_layers = h_layers,y =  y, classes_names = classes_names)

    print(str(y_predicted[1]) +" vs real: "+ str(y[1]))

    return mlp, y_predicted

def deeplearning_sae_sae(x_train_normal):

    ######## SPARSE AUTOENCODER TRAINING
    """ Define the parameters of the Autoencoder """
    rho            = 0.01   # desired average activation of hidden units... should be tuned!!
    lamda          = 0.0001 # weight decay parameter
    beta           = 3      # weight of sparsity penalty term
    max_iterations = 400    # number of optimization iterations
    visible_size = 41       # input & output sizes: KDDCup99 # of features
    hidden_size = 50        # sparse-autoencoder benefits from larger hidden layer units """
    """ Train and do a test over the same traindata """
    featured_x = execute_sparseAutoencoder(rho, lamda, beta, max_iterations, visible_size, hidden_size, x_train_normal)
    
        
    ######## SPARSE AUTOENCODER AND SOFTMAX FOR Classification
    """ Define the parameters of the Autoencoder """
    rho            = 0.01   # desired average activation of hidden units... should be tuned!!
    lamda          = 0.0001 # weight decay parameter
    beta           = 3      # weight of sparsity penalty term
    max_iterations = 400    # number of optimization iterations
    visible_size = 41       # input & output sizes: KDDCup99 # of features
    hidden_size = 16        # sparse-autoencoder benefits from larger hidden layer units """

    """ Train and do a test over the same traindata """
    y_prima = execute_sparseAutoencoder(rho, lamda, beta, max_iterations, visible_size, hidden_size, featured_x)
    y_predicted = softmax(y_prima)
    print(str(y_predicted[:, 1]))

    return y_predicted


###########################################################################

    
def main():
    #test soft max -solution
    #without normalization: [[ 0.00626879  0.01704033  0.04632042  0.93037047]
    #                       [ 0.01203764  0.08894682  0.24178252  0.65723302]
    #                       [ 0.00626879  0.01704033  0.04632042  0.93037047]]
    x2 = np.array([[1, 2, 3, 6],  # sample 1
               [2, 4, 5, 6],  # sample 2
               [1, 2, 3, 6]]) # sample 1 again(!)
    print(softmax(sparse_normalize_dataset(x2)))
    # LOAD KDD dataset 
    pre_data = np.transpose(kdd.simple_preprocessing_KDD())
    x_train, y, classes_names =  kdd.separate_classes(pre_data, kdd._ATTACK_INDEX_KDD)
    x_train_normal_s = sparse_normalize_dataset(x_train)
    x_train_normal = normalize_dataset(x_train)

    print("Data preprocessing results:" )
    print("indata "+str(pre_data.shape[1]))
    print("classfied "+str(x_train.shape[1]))
    print("normalized " +str(x_train_normal_s.shape[1]))
    print ("Output classes: ")
    for c in classes_names:
        print (c)


    """move = []
    for index in range(training_data.shape[1]):
        #np.append(move,training_data[:,index], axis = 0)
        move.append(training_data[:,index])
    move_mat= np.transpose(np.array(move))
    print (str(move_mat.shape[1]))"""
    
    #First deep learning architecture: SAE (feature selection) and MLP (classifier)
    mlp, y_n1 = deeplearning_sae_mlp(x_train_normal_s, y, classes_names)
    #No feature selection: Only MLP
    mlp_solo, y_standalone1 = ids_mlp(x_train_normal, y, classes_names)

    #Second deep learning architecture: SAE (feature selection) and SAE-softmax (classifier)
    y_n2 = deeplearning_sae_sae(x_train_normal_s)

    #Validation
    print("\nSAE and MLP Validation")
    analysis_functions.validation(mlp.classifier, x_train_normal_s, y_n1, y, classes_names)
    print("\nMLP only Validation")
    analysis_functions.validation(mlp_solo.classifier, x_train_normal, y_standalone1, y, classes_names)
    print("\nSAE and SAE-softmax Validation")
    analysis_functions.validation(None, x_train_normal_s, y_n1, y, classes_names)

   


if __name__ == "__main__":main() ## with if
