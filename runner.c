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

	char* ptr = malloc(idx_where+1);
	ptr = strndup(swp, idx_where+2);
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

	exedir = realloc(exedir, strlen(exedir));

	strcpy(python3buf, exedir);

	size_t p3bufsize = strlen(python3buf) + strlen(ENDPOINT) + strlen(exedir) + strlen(FILEPATH) + 3;
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
		size_t arg_size = strlen(arg);

		int quoted_arg = 0;
		if (strchr(arg, ' ') != NULL) {
			arg_size += 2;
			quoted_arg = 1;
		}

		int new_len = strlen(command) + 1 + arg_size;

		command = realloc(command, new_len);
		strcat(command, " ");
		if (quoted_arg) {
			strcat(command, "\"");
		}

		strcat(command, arg);

		if (quoted_arg) {
			strcat(command, "\"");
		}
	}

	system(command);
}
