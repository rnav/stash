#define _GNU_SOURCE
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdio.h>
#include <sched.h>
#include <unistd.h>

int main()
{
	int pipe1[2], pipe2[2];
	char tracebuf[256];
	cpu_set_t cpus;
	int buf = 65;
	int tracefd;
	int fd, len;

	if (pipe(pipe1) || pipe(pipe2)) {
		perror("pipe");
		return -1;
	}

	tracefd = open("/sys/kernel/debug/tracing/trace_marker", O_WRONLY);
	if (tracefd < 0) {
		perror("open trace_marker");
		return -1;
	}

	fd = fork();
	if (fd == -1) {
		perror("fork");
		return -1;
	}

	CPU_ZERO(&cpus);
	if (fd == 0) {
		len = snprintf(tracebuf, 256, "in child");
		write(tracefd, &tracebuf, len);

		CPU_SET(6, &cpus);
		if (sched_setaffinity(0, sizeof(&cpus), &cpus)) {
			perror("sched_setaffinity");
			return -1;
		}
		close(pipe1[1]);
		close(pipe2[0]);

		len = snprintf(tracebuf, 256, "child read pipe1");
		write(tracefd, &tracebuf, len);

		read(pipe1[0], &buf, 1);
		close(pipe1[0]);

		len = snprintf(tracebuf, 256, "child write pipe2");
		write(tracefd, &tracebuf, len);

		write(pipe2[1], &buf, 1);
		close(pipe2[1]);

		len = snprintf(tracebuf, 256, "child done");
		write(tracefd, &tracebuf, len);
	} else {
		len = snprintf(tracebuf, 256, "in parent");
		write(tracefd, &tracebuf, len);

		CPU_SET(4, &cpus);
		if (sched_setaffinity(0, sizeof(&cpus), &cpus)) {
			perror("sched_setaffinity");
			return -1;
		}
		close(pipe1[0]);
		close(pipe2[1]);

		len = snprintf(tracebuf, 256, "parent write pipe1");
		write(tracefd, &tracebuf, len);

		write(pipe1[1], &buf, 1);
		close(pipe1[1]);

		len = snprintf(tracebuf, 256, "parent read pipe2");
		write(tracefd, &tracebuf, len);

		read(pipe2[0], &buf, 1);
		close(pipe2[0]);

		len = snprintf(tracebuf, 256, "parent done");
		write(tracefd, &tracebuf, len);
	}

	return 0;
}

