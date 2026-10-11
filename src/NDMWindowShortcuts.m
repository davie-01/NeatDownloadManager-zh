#import <AppKit/AppKit.h>

// This is a local monitor inside NDM, not a system-wide shortcut or key logger.
BOOL NDMIsCloseShortcut(NSEvent *event) {
    if (event.type != NSEventTypeKeyDown) return NO;
    NSEventModifierFlags modifiers = event.modifierFlags &
        (NSEventModifierFlagCommand | NSEventModifierFlagControl |
         NSEventModifierFlagOption | NSEventModifierFlagShift);
    return modifiers == NSEventModifierFlagCommand &&
        [event.charactersIgnoringModifiers.lowercaseString isEqualToString:@"w"];
}

static NSButton *NDMDismissButton(NSView *view) {
    if (view.hidden) return nil;
    if ([view isKindOfClass:NSButton.class]) {
        NSButton *button = (NSButton *)view;
        NSString *action = NSStringFromSelector(button.action).lowercaseString;
        NSString *title = button.title.lowercaseString;
        BOOL dismiss = [action containsString:@"cancel"] || [action containsString:@"close"] ||
            [@[@"cancel", @"close", @"取消", @"关闭"] containsObject:title];
        if (button.enabled && dismiss) return button;
    }
    for (NSView *child in view.subviews) {
        NSButton *button = NDMDismissButton(child);
        if (button) return button;
    }
    return nil;
}

BOOL NDMDismissWindow(NSWindow *window) {
    if (!window) return NO;
    // A sheet takes precedence over the underlying main window.
    if (window.attachedSheet) window = window.attachedSheet;
    if (window.sheetParent) {
        NSButton *dismiss = NDMDismissButton(window.contentView);
        if (dismiss) {
            [dismiss performClick:nil];
        } else {
            [NSApp endSheet:window returnCode:NSModalResponseCancel];
            [window orderOut:nil];
        }
        return YES;
    }
    if (window.styleMask & NSWindowStyleMaskClosable) {
        // Preserve the window's own delegate and close-button behavior.
        [window performClose:nil];
        return YES;
    }
    return NO;
}

#ifndef NDM_SHORTCUT_TEST
__attribute__((constructor)) static void NDMInstallWindowShortcuts(void) {
    dispatch_async(dispatch_get_main_queue(), ^{
        static id monitor;
        monitor = [NSEvent addLocalMonitorForEventsMatchingMask:NSEventMaskKeyDown handler:^NSEvent *(NSEvent *event) {
            if (!NDMIsCloseShortcut(event)) return event;
            // Holding the shortcut must not close successive windows.
            if (event.isARepeat) return nil;
            NSWindow *window = NSApp.keyWindow ?: event.window ?: NSApp.mainWindow;
            return NDMDismissWindow(window) ? nil : event;
        }];
    });
}
#endif
