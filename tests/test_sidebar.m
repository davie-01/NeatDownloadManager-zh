#import <Foundation/Foundation.h>
#import <CoreFoundation/CoreFoundation.h>
#import <objc/message.h>
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "hook-offsets.h"

@interface Sink : NSObject
@property (nonatomic, copy) NSString *value;
- (void)setStringValue:(NSString *)value;
@end
@implementation Sink
- (void)setStringValue:(NSString *)value { self.value = value; }
@end

static void write32(void *p, uint32_t value) { memcpy(p, &value, 4); }

int main(int argc, char **argv) {
    @autoreleasepool {
        if (argc != 2) return 2;
        FILE *f = fopen(argv[1], "rb");
        if (!f) return 2;
        unsigned char *memory = mmap(NULL, 4096, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANON, -1, 0);
        if (memory == MAP_FAILED) { perror("mmap"); return 2; }
        fread(memory, 1, 1792, f);
        fclose(f);
        SEL eq = sel_registerName("isEqualToString:");
        SEL utf8 = sel_registerName("stringWithUTF8String:");
        Class nsstring = [NSString class];
        memcpy(memory+2048, &eq, 8);
        memcpy(memory+2056, &utf8, 8);
        memcpy(memory+2064, &nsstring, 8);
        void *send = (void *)objc_msgSend;
#if defined(__aarch64__)
        write32(memory+2080, 0x58000050); // ldr x16, literal +8
        write32(memory+2084, 0xd61f0200); // br x16
        memcpy(memory+2088, &send, 8);
#else
        memcpy(memory+2080, &send, 8);
#endif
        NSArray *english = @[@"Complete", @"Incomplete", @"All Downloads", @"Video", @"Audio", @"Compressed", @"Document", @"Misc"];
        NSArray *chinese = @[@"已完成", @"未完成", @"全部下载", @"视频", @"音频", @"压缩包", @"文档", @"其他"];
        // Copy real constant-string records: pointers remain owned by this test binary.
        const void *constants[] = {CFSTR("Complete"), CFSTR("Incomplete"), CFSTR("All Downloads"),
            CFSTR("Video"), CFSTR("Audio"), CFSTR("Compressed"), CFSTR("Document"), CFSTR("Misc")};
        for (int i=0; i<8; ++i) memcpy(memory+2112+i*32, constants[i], 32);
        for (int i = 0; i < sizeof(offsets)/sizeof(offsets[0]); ++i) {
            int offset = offsets[i];
            intptr_t delta = targets[i] - offset;
#if defined(__aarch64__)
            uint32_t instruction;
            if (kinds[i] >= 2) {
                instruction = (kinds[i] == 3 ? 0x14000000 : 0x94000000) | ((delta / 4) & 0x03ffffff);
            } else if (kinds[i] == 1) {
                instruction = 0x10000002 | ((delta & 3) << 29) | (((delta >> 2) & 0x7ffff) << 5);
            } else {
                instruction = 0x58000000 | (((delta / 4) & 0x7ffff) << 5) | registers[i];
            }
            write32(memory+offset, instruction);
#else
            int size = kinds[i] >= 2 ? 6 : 7;
            int32_t relative = (int32_t)(delta - size);
            memcpy(memory+offset+size-4, &relative, 4);
#endif
        }
        __builtin___clear_cache((char *)memory, (char *)memory+2400);
        if (mprotect(memory, 4096, PROT_READ | PROT_EXEC)) { perror("mprotect"); return 2; }
        void (*hook)(id, SEL, NSString *) = (void *)memory;
        Sink *sink = [Sink new];
        NSArray *inputs = [english arrayByAddingObjectsFromArray:@[@"全部下载", @"视频", @"Completed", @""]];
        NSArray *expected = [chinese arrayByAddingObjectsFromArray:@[@"全部下载", @"视频", @"Completed", @""]];
        for (NSUInteger i=0; i<inputs.count; ++i) {
            hook(sink, @selector(setStringValue:), inputs[i]);
            if (![sink.value isEqualToString:expected[i]]) {
                NSLog(@"FAIL: %@ -> %@ expected %@", inputs[i], sink.value, expected[i]);
                return 1;
            }
        }
        hook(sink, @selector(setStringValue:), nil);
        if (sink.value != nil) return 1;
        puts("PASS: actual hook translates the eight sidebar labels without changing internal values; other strings and nil preserved");
        munmap(memory, 4096);
    }
    return 0;
}
