#include <stdio.h>
#include <stdlib.h>
#include <zlib.h>
#include <stdint.h>

int32_t initialize(gzFile, int);
int32_t countup(gzFile, int32_t, int32_t, int32_t *);
void countup_residuals(int32_t, int32_t, int32_t *);
void countup_subsites(int32_t, int32_t *);
void site_to_string(int32_t, int, char *);
void print_counts(FILE *, int, int32_t *);

int main(int argc, char **argv){
	if(argc != 4){
		printf("usage: ./count_words word_length input.fasta[.gz] output.cnt\n");
		return 1;
	}
	const int len = atoi(argv[1]);
	if(len < 1 || len > 14){
		printf("bad word length, only [1..14] is allowed\n");
		return 1;
	}
	gzFile fasta;
	fasta = gzopen(argv[2], "rb");
	if(fasta == NULL){
		printf("fasta file was not found\n");
		return 1;
	}
	FILE *cnt;
	cnt = fopen(argv[3], "wb");
	if(cnt == NULL){
		printf("can't create output file\n");
		return 1;
	}
	int32_t num = 1 << (len * 2 + 1);
	int32_t *counts;
	counts = (int32_t *)calloc(num, sizeof(int32_t));
	if(counts == NULL){
		printf("can't allocate memory for counts\n");
		return 2;
	}
	int32_t mask = (num >> 1) - 1;
	while(1){
		if(skip(fasta) == 0)
			break;
		int32_t site = countup(fasta, initialize(fasta, len), mask, counts);
		countup_residuals(site, mask, counts);
	}
	countup_subsites(num-1, counts);
	print_counts(cnt, len, counts);
	free(counts);
	if(!gzeof(fasta)){
		printf("fasta file reading error\n");
		return 3;
	}
	if(gzclose(fasta) < 0){
		printf("fasta file closing error\n");
		return 3;
	}
	if(fclose(cnt) < 0){
		printf("output file closing error\n");
		return 3;
	}
}

int translate(char nucl){
	switch(nucl){
		case 'A': case 'a': return 0;
		case 'C': case 'c': return 1;
		case 'G': case 'g': return 2;
		case 'T': case 't': return 3;
		case '\n': case '\t': case ' ': case '-': return -2;
		default: return -1;
	}
}

int skip(gzFile fasta){
	int nucl;
	while((nucl = gzgetc(fasta)) != -1){
		if(nucl == '>'){
			while((nucl = gzgetc(fasta)) != '\n')
				if(nucl == -1)
					return 0;
			continue;
		}
		if(translate(nucl) >= 0){
			gzungetc(nucl, fasta);
			return 1;
		}
	}
	return 0;
}

int32_t initialize(gzFile fasta, int len){
	int32_t site = 1;
	int i, nucl;
	for(i=0; i<len;){
		if((nucl = gzgetc(fasta)) == -1)
			return site;
		int tnucl = translate(nucl);
		if(tnucl < -1)
			continue;
		if(tnucl >= 0){
			site = (site << 2) + tnucl;
			i += 1;
		}else{
			gzungetc(nucl, fasta);
			return site;
		}
	}
	return site;
}

int32_t countup(gzFile fasta, int32_t site, int32_t mask, int32_t *counts){
	int nucl;
	while((nucl = gzgetc(fasta)) != -1){
		int tnucl = translate(nucl);
		if(tnucl < -1)
			continue;
		if(tnucl >= 0){
			counts[site] += 1;
			site = (((site << 2) + tnucl) & mask) + mask + 1;
		}else{
			gzungetc(nucl, fasta);
			return site;
		}
	}
	return site;
}

void countup_residuals(int32_t site, int32_t mask, int32_t *counts){
	while(mask > site)
		mask >>= 2;
	while(mask != 0){
		site = (site & mask) + mask + 1;
		counts[site] += 1;
		mask >>= 2;
	}
}

void countup_subsites(int32_t max, int32_t *counts){
	int32_t min = max >> 1;
	int32_t site;
	while(min != 0){
		for(site = max; site > min; site -= 1)
			counts[site>>2] += counts[site];
		max >>= 2;
		min = max >> 1;
	}
}

void site_to_string(int32_t site, int len, char *dest){
	const char nucls[] = {'A', 'C', 'G', 'T'};
	int i = len - 1;
	while(site != 1){
		dest[i] = nucls[site & 3];
		site >>= 2;
		i -= 1;
	}
}

void print_counts(FILE *cnt, int len, int32_t *counts){
	const char nucls[] = {'A', 'C', 'G', 'T'};
	int i = 1;
	int32_t from = 1 << 2;
	int32_t to = from << 1;
	for(; i<=len; i++){
		int32_t site;
		char dest[i+1];
		dest[i] = '\0';
		for(site=from; site<to; site++){
			site_to_string(site, i, dest);
			fprintf(cnt, "%s\t%d\n", dest, counts[site]);
		}
		from <<= 2;
		to <<= 2;
	}
}

