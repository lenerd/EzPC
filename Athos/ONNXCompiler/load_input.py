
'''

Authors: Shubham Ugare.

Copyright:
Copyright (c) 2018 Microsoft Research
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''

import numpy.random
import numpy as np
import common
import os, sys
import onnx
from onnx import helper
import math
from onnx import numpy_helper

def main():
    if (len(sys.argv) < 3):
        print("Model file or scaling factor unspecified.", file=sys.stderr)
        exit(1)
    
    file_name = sys.argv[1]
    scaling_factor = int(sys.argv[2])
    inp_path = sys.argv[3]
    file_path = 'models/' + file_name
    model_name = file_name[:-5] # name without the '.onnx' extension
    model = onnx.load(file_path)
    print("Model loaded")
    graph_def = model.graph
    
    # Generating input
    input_dims = common.proto_val_to_dimension_tuple(model.graph.input[0])
    if(input_dims[0] == 0):
        input_dims = list(input_dims) 
        input_dims[0] = 1  # when batch size is not defined
        input_dims = tuple(input_dims)
    input_array = numpy.random.random(input_dims)
    input_array_raw = np.load('debug/' + model_name + '/'+ inp_path)
    input_array_raw = input_array_raw.astype(np.float32)
    print(input_array_raw.shape, input_array.shape)
    for i in range(len(input_array_raw)):
        for j in range(len(input_array_raw[i])):
            for k in range(len(input_array_raw[i][j])):
                # print(0, i, j, k)
                # print(input_array_raw[i][j][k])
                input_array[0][i][j][k] = input_array_raw[i][j][k]
    # input_array = numpy.ones(input_dims, dtype=float) 
    print('Generated random input of dimension ' + str(input_dims))
    np.save('debug/' + model_name + '/' + model_name + '_input', input_array)

    (chunk_inp, cnt) = common.numpy_float_array_to_fixed_point_val_str(input_array, scaling_factor)
    
    #Save the input file for client
    f = open('debug/' + model_name + '/' + model_name + '_input_client.clr', 'w') 
    f.write(chunk_inp)
    f.close()
    chunk = ""
    print("Input image written to file")

    model_name_to_val_dict = { init_vals.name: numpy_helper.to_array(init_vals).tolist() for init_vals in model.graph.initializer}

    preprocess_batch_normalization(graph_def, model_name_to_val_dict)

    for init_vals in model.graph.initializer:
        (chunk_1, cnt_1) = common.numpy_float_array_to_fixed_point_val_str(
            np.asarray(model_name_to_val_dict[init_vals.name], dtype=np.float32), scaling_factor)
        chunk += chunk_1
        cnt += cnt_1

    f = open('debug/' + model_name + '/' + model_name + '_input_server.clr', 'w') 
    f.write(chunk)
    f.close()
    print("Model weights written to file")

    print('Total ' + str(cnt) + ' integers were written in ' + model_name + '_input.h')

def preprocess_batch_normalization(graph_def, model_name_to_val_dict):
    # set names to graph nodes if not present
    for node in graph_def.node: 
        node.name = node.output[0]
        # Update the batch normalization scale and B
        # so that mean and var are not required
        if(node.op_type == 'BatchNormalization'):
            # scale
            gamma = model_name_to_val_dict[node.input[1]]
            # B
            beta = model_name_to_val_dict[node.input[2]]
            mean = model_name_to_val_dict[node.input[3]]
            var = model_name_to_val_dict[node.input[4]]
            for i in range(len(gamma)):
                rsigma = 1/math.sqrt(var[i]+1e-5)
                gamma[i] = gamma[i]*rsigma
                beta[i] = beta[i]-gamma[i]*mean[i]  
                mean[i] = 0
                var[i] = 1-1e-5

    # Just testing if the correct values are put            
    model_name_to_val_dict2 = {}
    for init_vals in graph_def.initializer:
        # TODO: Remove float_data
        model_name_to_val_dict2[init_vals.name] = init_vals.float_data      
    for node in graph_def.node: 
        node.name = node.output[0]
        if(node.op_type == 'BatchNormalization'):
            mean = model_name_to_val_dict[node.input[3]]
            for val in mean:
                assert(val == 0)

if __name__ == "__main__":
    main()                                          
