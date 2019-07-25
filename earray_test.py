import numpy as np
import tables
import time

test_img = np.random.rand(640,480,3)
total_images = 1000

hf5_path = 'hf5_file.hf5'
hf5 = tables.open_file(hf5_path, mode = 'w')
filters = tables.Filters(complevel=5, complib='blosc')
data_storage = hf5.create_earray('/','data',
                        tables.Atom.from_dtype(test_img.dtype),
                        shape = (0, test_img.shape[0],test_img.shape[1],test_img.shape[2]),
                        filters = filters,
                        expectedrows = total_images)

array = np.random.random((total_images,640,480,3)) 

start_t = time.time()
for i in range(total_images):
    data_storage.append(array[i,:,:,:][None])
end_t = time.time()
print(end_t - start_t)

hf5.close()


start_t = time.time()
for i in range(total_images):
    np.save('write_test/file{}'.format(i),array[i,:,:,:])
end_t = time.time()
print(end_t - start_t)
