#include "Python.h"
#include <stdio.h>

static PyObject *cspritelib_parse_header(PyObject *self, PyObject *args) {
    PyObject *p = NULL;

    int signature, width, height, frame_count;
    int uk_1, uk_2;
    PyListObject *offsets = NULL;
    PyStringObject *size_dummy = NULL;

    FILE *fp = NULL;
    int *_offsets = NULL;
    unsigned char *_size_dummy;
    int index, size, small_size, store_size_dummy = 0;

    if(!PyArg_ParseTuple(args, "O", &p)) {
        return NULL;
    }

    fp = PyFile_AsFile(p);
    PyFile_IncUseCount((PyFileObject *)p);
    Py_BEGIN_ALLOW_THREADS

    fseek(fp, 0, SEEK_SET);

    fread(&signature, sizeof(int), 1, fp);
    if(signature != 9) {
        Py_RETURN_NONE;
    }

    fread(&width, sizeof(int), 1, fp);
    fread(&height, sizeof(int), 1, fp);
    fread(&frame_count, sizeof(int), 1, fp);

    _offsets = (int *)malloc(sizeof(int) * (frame_count + 1));
    for(index = 0; index < frame_count; ++index) {
        fseek(fp, 0x4c0 + index * 4, SEEK_SET);
        fread(&_offsets[index], sizeof(int), 1, fp);
    }

    fseek(fp, 0xbc8, SEEK_SET);
    fread(&_offsets[frame_count], sizeof(int), 1, fp);

    _size_dummy = (unsigned char *)malloc(sizeof(unsigned char) * (frame_count * 2));
    for(index = 0; index < frame_count; ++index) {
        size = _offsets[index + 1] - _offsets[index];
        small_size = size - ((size >> 8) << 8);

        fseek(fp, 0x970 + index * 2, SEEK_SET);
        fread(&_size_dummy[index * 2], sizeof(short), 1, fp);

        if(small_size != *(short *)&_size_dummy[index * 2] && !store_size_dummy) {
            store_size_dummy = 1;
        }
    }

    fseek(fp, 0xbcc, SEEK_SET);
    fread(&uk_1, sizeof(int), 1, fp);
    fread(&uk_2, sizeof(int), 1, fp);

    Py_END_ALLOW_THREADS
    PyFile_DecUseCount((PyFileObject *)p);

    offsets = (PyListObject *)PyList_New(0);
    for(index = 0; index < frame_count; ++index) {
        PyList_Append((PyObject *)offsets, PyInt_FromLong(_offsets[index]));
    }

    if(store_size_dummy) {
        size_dummy = (PyStringObject *)PyString_FromStringAndSize((const char *)_size_dummy, frame_count * 2);
    }
    else {
        size_dummy = (PyStringObject *)PyString_FromString("");
    }

    free(_offsets);
    free(_size_dummy);

    return Py_BuildValue("iiiiiOO", width, height, frame_count, uk_1, uk_2, size_dummy, offsets);
}
static PyObject *cspritelib_parse_frame(PyObject *self, PyObject *args) {
    PyObject *p = NULL;
    int width, height, offset;

    PyStringObject *frame = NULL;

    FILE *fp = NULL;
    unsigned char *_frame = NULL, byte, repeat;
    int i, j;

    if(!PyArg_ParseTuple(args, "Oiii", &p, &width, &height, &offset)) {
        return NULL;
    }

    fp = PyFile_AsFile(p);
    PyFile_IncUseCount((PyFileObject *)p);
    Py_BEGIN_ALLOW_THREADS

    fseek(fp, 0xbf4 + offset, SEEK_SET);

    _frame = (unsigned char *)malloc(sizeof(unsigned char) * (width * height));
    for(i = 0; i < height; ++i) {
        for(j = 0; j < width;) {
            fread(&byte, sizeof(unsigned char), 1, fp);
            if(byte == 0xfe) {
                fread(&repeat, sizeof(unsigned char), 1, fp);
                while(repeat > 0) {
                    _frame[i * width + j] = byte;
                    ++j;
                    --repeat;
                }
            }
            else {
                _frame[i * width + j] = byte;
                ++j;
            }
        }
    }

    Py_END_ALLOW_THREADS
    PyFile_DecUseCount((PyFileObject *)p);

    frame = (PyStringObject *)PyString_FromStringAndSize((const char *)_frame, width * height);

    free(_frame);

    return Py_BuildValue("O", frame);
}
static PyObject *cspritelib_save_file(PyObject *self, PyObject *args) {
    PyListObject *frames;
    PyStringObject *size_dummy;
    int width, height, frame_count, uk_1, uk_2;

    const char *path = NULL;
    FILE *fp = NULL;
    unsigned char *frame = NULL;
    int total_size = 0, size;
    int index, i, j, k;
    short small_size;
    int write_size_dummy;

    if(!PyArg_ParseTuple(args, "siiiiiOO", &path, &width, &height, &frame_count, &uk_1, &uk_2, &frames, &size_dummy)) {
        return NULL;
    }

    fp = fopen(path, "wb");

    fseek(fp, 0, SEEK_SET);
    i = 9;
    fwrite(&i, sizeof(int), 1, fp);
    fwrite(&width, sizeof(int), 1, fp);
    fwrite(&height, sizeof(int), 1, fp);
    fwrite(&frame_count, sizeof(int), 1, fp);
    fseek(fp, 0xbcc, SEEK_SET);
    fwrite(&uk_1, sizeof(int), 1, fp);
    fwrite(&uk_2, sizeof(int), 1, fp);

    write_size_dummy = (PyString_Size((PyObject *)size_dummy) > 0);

    for(index = 0; index < frame_count; ++index) {
        frame = (unsigned char *)PyByteArray_AsString(PyList_GetItem((PyObject *)frames, index));

        fseek(fp, 0x4c0 + index * 4, SEEK_SET);
        fwrite(&total_size, sizeof(int), 1, fp);

        fseek(fp, 0xbf4 + total_size, SEEK_SET);
        size = 0;
        for(i = 0; i < height; ++i) {
            for(j = 0; j < width;) {
                if(frame[i * width + j] == 0xfe) {
                    for(k = 0; k < 255 && j + k < width && frame[i * width + j + k] == 0xfe; ++k);
                    fwrite(&frame[i * width + j], sizeof(unsigned char), 1, fp);
                    fwrite(&k, sizeof(unsigned char), 1, fp);

                    size += 2;
                    j += k - 1;
                }
                else {
                    fwrite(&frame[i * width + j], sizeof(unsigned char), 1, fp);
                    ++size;
                }
                ++j;
            }
        }

        if(!write_size_dummy) {
            fseek(fp, 0x970 + index * 2, SEEK_SET);
            small_size = size - ((size >> 8) << 8);
            fwrite(&small_size, sizeof(short), 1, fp);
        }

        total_size += size;
    }

    if(write_size_dummy) {
        fseek(fp, 0x970, SEEK_SET);
        fwrite(PyString_AsString((PyObject *)size_dummy), sizeof(unsigned char), frame_count * 2, fp);
    }

    fseek(fp, 0xbc8, SEEK_SET);
    fwrite(&total_size, sizeof(int), 1, fp);

    fclose(fp);

    Py_RETURN_NONE;
}

static struct PyMethodDef module_methods[] = {
    {"c_parse_header", cspritelib_parse_header, METH_VARARGS},
    {"c_parse_frame", cspritelib_parse_frame, METH_VARARGS},
    {"c_save_file", cspritelib_save_file, METH_VARARGS},
    {NULL,}
};

PyMODINIT_FUNC initcspritelib() {
    Py_InitModule("cspritelib", module_methods);
}