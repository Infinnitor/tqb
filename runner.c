#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/param.h>


#define ENDPOINT "venv/bin/python3"
#define FILEPATH "src/main.py"
#define DEFAULT_BUF 0x100


char* trim_ws(char* src) {
	int length = strlen(src);
	char* swp = malloc(length);

	int idx = 0;
	int trail = 0;

	for (int i = 0; i < length; i++) {
		if (src[i] == ' ') {
			if (trail == 1) {
				swp[idx] = src[i];
				idx++;
			}
		}

		else {
			trail = 1;
			swp[idx] = src[i];
			idx++;
		}
	}

	char* src_rev = malloc(idx);
	strcpy(src_rev, swp);

	trail = 0;
	int idx_where;

	for (int i = idx-1; i > -1; i--) {
		if (src_rev[i] != ' ') {
			idx_where = i;
			break;
		}
	}

	char* ptr = strndup(swp, idx_where+1);
	free(src_rev);
	free(swp);

	return ptr;
}



char* dir(const char* path) {
	char* last_slash = strrchr(path, '/');
	if (last_slash == NULL) {
		return ".";
	}
	char* ptr = strndup(path, (size_t)last_slash - (size_t)path);
	return ptr;
}



int main(int argc, char** argv) {
	char* exebuf = malloc(DEFAULT_BUF);
	char* exedir = malloc(DEFAULT_BUF);
	char* python3buf = malloc(DEFAULT_BUF);

	int pathlen = MIN(readlink("/proc/self/exe", exebuf, DEFAULT_BUF), DEFAULT_BUF - 1);
	if (pathlen >= 0) {
		exebuf[pathlen] = '\0';
	}

	strcpy(exedir, exebuf);
	char* ptr = dir(trim_ws(exebuf));
	strcpy(exedir, ptr);
	/* printf("%s|\n", exedir); */

	exedir = realloc(exedir, strlen(exedir));

	strcpy(python3buf, exedir);

	size_t p3bufsize = strlen(python3buf) + strlen(ENDPOINT) + strlen(FILEPATH) + 3;
	python3buf = realloc(python3buf, p3bufsize);
	strcat(python3buf, "/");
	strcat(python3buf, ENDPOINT);
	strcat(python3buf, " ");
	strcat(python3buf, exedir);
	strcat(python3buf, "/");
	strcat(python3buf, FILEPATH);

	char* command = malloc(p3bufsize);
	strcpy(command, python3buf);

	for (int i=1; i<argc; i++) {
		char* arg = argv[i];
		int new_len = strlen(command) + 1 + strlen(arg);

		command = realloc(command, new_len);
		strcat(command, " ");
		strcat(command, arg);
	}

	printf("%s\n", command);

	system(command);
}
