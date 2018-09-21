#include <Python.h>
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>

#include <cmath>
#include <iostream>

using namespace std;

/*****************************************************************************
 * Array access macros.                                                      *
 *****************************************************************************/
#define v3(a, x0, x1, x2) (*(npy_float64*)(PyArray_BYTES(a) +   \
                            (x0) * PyArray_STRIDE(a, 0) +   \
                            (x1) * PyArray_STRIDE(a, 1) +   \
                            (x2) * PyArray_STRIDE(a, 2)))
#define s(a, i) (PyArray_DIM(a, i))

void compute_cpp(PyArrayObject *img,
                 double dist,
                 double* steer,
                 double* throttle) {
  // cerr << "Arr dims: " << s(img, 0) << ' ' << s(img, 1) << ' ' << s(img, 2) << endl;
  double rs = 0.0 , rp = 1.0;
  for (int i=0; i<s(img, 0); i++)
    for (int j=0; j<s(img, 1); j++)
      for (int z=0; z<s(img, 2); z++) {
        rs += v3(img, i, j, z);
        rp *= v3(img, i, j, z);
      }
  *steer = rs;
  *throttle = rp;
  return;
}


extern "C" {
  // Forward function declaration.
  static PyObject *compute(PyObject *self, PyObject *args); 

  // Boilerplate: method list.
  static PyMethodDef methods[] = {
    { "compute", compute, METH_VARARGS,
    "Compute steer and throttle. Input is one 3d numpy array.\n"
    "Output is a pair of floats between -1 and 1, or None."
    },
    { NULL, NULL, 0, NULL } /* Sentinel */
  };

  static struct PyModuleDef module = {
      PyModuleDef_HEAD_INIT,
      "cext_cpp",   /* name of module */
      NULL, /* module documentation, may be NULL */
      -1,       /* size of per-interpreter state of the module,
                  or -1 if the module keeps state in global variables. */
      methods
  };

  // Boilerplate: Module initialization.
  PyMODINIT_FUNC
  PyInit_cext(void)
  {
      PyObject *m;

      m = PyModule_Create(&module);
      if (m == NULL)
          return NULL;
      import_array();
      return m;
  }

  static PyObject *compute(PyObject *self, PyObject *args) {
    npy_float64 dist, steer, throttle;
    PyArrayObject *img;

    // Parse arguments. 
    if (!PyArg_ParseTuple(args, "O!d",
                          &PyArray_Type, &img,
                          &dist)) {
      return NULL;
    }

    if (PyArray_NDIM(img) != 3) {
      PyErr_SetString(PyExc_ValueError, "Expecting 3d (RGB) array");
      return NULL;
    }
    
    Py_BEGIN_ALLOW_THREADS
    compute_cpp(img, dist, &steer, &throttle);
    Py_END_ALLOW_THREADS

    // return PyFloat_FromDouble(0.0);
    return Py_BuildValue(
      "OO", 
      PyFloat_FromDouble(steer), 
      PyFloat_FromDouble(throttle)
    );
  }
}

