/* Biquad low-pass (Butterworth, fc = 0.2 x Nyquist), transposed direct form II.
 *
 * Calling convention understood by dsp_props.adapters:
 *   void f(const double *x, size_t n, double *y, double *state)
 * The state (2 doubles) carries the filter memory from one block to the next.
 */
#include <stddef.h>

static const double B[3] = {0.06745527388907189, 0.13491054777814378, 0.06745527388907189};
static const double A[3] = {1.0, -1.1429805025399011, 0.41280159809618877};

void biquad(const double *x, size_t n, double *y, double *s)
{
    for (size_t i = 0; i < n; i++) {
        double out = B[0] * x[i] + s[0];
        s[0] = B[1] * x[i] - A[1] * out + s[1];
        s[1] = B[2] * x[i] - A[2] * out;
        y[i] = out;
    }
}

/* Bug: the accumulator is single precision. */
void biquad_float_acc(const double *x, size_t n, double *y, double *s)
{
    for (size_t i = 0; i < n; i++) {
        float out = (float)(B[0] * x[i] + s[0]);
        s[0] = B[1] * x[i] - A[1] * out + s[1];
        s[1] = B[2] * x[i] - A[2] * out;
        y[i] = out;
    }
}

/* Bug: the second state variable is not carried across blocks (local copy). */
void biquad_drops_state(const double *x, size_t n, double *y, double *s)
{
    double s1 = 0.0;
    for (size_t i = 0; i < n; i++) {
        double out = B[0] * x[i] + s[0];
        s[0] = B[1] * x[i] - A[1] * out + s1;
        s1 = B[2] * x[i] - A[2] * out;
        y[i] = out;
    }
}
