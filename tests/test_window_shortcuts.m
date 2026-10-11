#import <AppKit/AppKit.h>
#import "../src/NDMWindowShortcuts.m"

@interface FakeView : NSObject
@property (getter=isHidden) BOOL hidden;
@property NSArray *subviews;
@end
@implementation FakeView
@end

@interface FakeButton : FakeView
@property (getter=isEnabled) BOOL enabled;
@property SEL action;
@property NSString *title;
@property BOOL clicked;
@end
@implementation FakeButton
- (BOOL)isKindOfClass:(Class)class { return class == NSButton.class || [super isKindOfClass:class]; }
- (void)performClick:(id)sender { self.clicked = YES; }
@end

@interface FakeWindow : NSObject
@property FakeWindow *attachedSheet;
@property FakeWindow *sheetParent;
@property FakeView *contentView;
@property NSWindowStyleMask styleMask;
@property BOOL closed;
@end
@implementation FakeWindow
- (void)performClose:(id)sender { self.closed = YES; }
@end

static void check(BOOL pass, NSString *message) {
    if (!pass) { NSLog(@"FAIL: %@", message); exit(1); }
}
static NSEvent *key(NSString *characters, NSEventModifierFlags flags) {
    return [NSEvent keyEventWithType:NSEventTypeKeyDown location:NSZeroPoint modifierFlags:flags
        timestamp:0 windowNumber:0 context:nil characters:characters charactersIgnoringModifiers:characters isARepeat:NO keyCode:13];
}
int main(void) {
    @autoreleasepool {
        check(NDMIsCloseShortcut(key(@"w", NSEventModifierFlagCommand)), @"Command W");
        check(NDMIsCloseShortcut(key(@"W", NSEventModifierFlagCommand | NSEventModifierFlagCapsLock)), @"Caps Lock");
        check(!NDMIsCloseShortcut(key(@"w", 0)), @"plain w preserved");
        check(!NDMIsCloseShortcut(key(@"w", NSEventModifierFlagCommand | NSEventModifierFlagOption)), @"Option combination preserved");
        check(!NDMIsCloseShortcut(key(@"w", NSEventModifierFlagCommand | NSEventModifierFlagShift)), @"Shift combination preserved");
        check(!NDMIsCloseShortcut(key(@"c", NSEventModifierFlagCommand)), @"copy shortcut preserved");
        FakeWindow *main = [FakeWindow new]; main.styleMask = NSWindowStyleMaskClosable;
        check(NDMDismissWindow((id)main) && main.closed, @"main follows existing close action");
        main.closed = NO;
        FakeButton *cancel = [FakeButton new]; cancel.enabled = YES; cancel.action = @selector(btnCancelClicked:); cancel.title = @"取消";
        FakeView *view = [FakeView new]; view.subviews = @[(id)cancel];
        FakeWindow *sheet = [FakeWindow new]; sheet.sheetParent = main; sheet.contentView = (id)view;
        main.attachedSheet = sheet;
        check(NDMDismissWindow((id)main) && cancel.clicked && !main.closed, @"sheet canceled without closing parent");
        check(!NDMDismissWindow(nil), @"no window preserved");
        puts("PASS: shortcut modifiers, original close action, sheet cancellation, parent preservation");
    }
}
