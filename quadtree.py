import time
import math
import random
import pygame


class Point:
    '''
    Represents a point on 2D plane. 
    '''

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Point):
            return self.x == __value.x and self.y == __value.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self) -> str:
        return f'Point({self.x}, {self.y})'


class QuadNode:
    '''
    Represent a node in Quad Tree.

    Fields:
        id:


    A node can either contain children nodes(self.children) or points(self.points).

    Order of children are as follows:
        0 1
        2 3

    1st child is at index 0, 2nd at index 1...


    '''
    SPLIT_THRESHOLD = 1

    def __init__(self, w: int, h: int, id: list[int], x: int = 0, y: int = 0, parent: 'QuadNode' = None) -> None:
        '''
        children:
            0 1
            2 3
        '''
        self.id = id
        self.w = w
        self.h = h
        self.x = x
        self.y = y
        self.parent = parent

        self.children: list[QuadNode] = []
        self.points: list[Point] = []

    def has_children(self) -> bool:
        '''
        Check if the node has children
        '''
        return len(self.children) > 0

    def insert(self, point: Point) -> None:
        '''
        Insert a point into the quad tree
        '''
        if point.x < self.x or point.x >= self.x + self.w or point.y < self.y or point.y >= self.y + self.h:
            print(self.x, self.y, self.w, point, self.id)
            raise ValueError('Point is out of range')

        if self.has_children():
            idx = int(point.x >= self.x + self.w // 2) + int(point.y >= self.y + self.h // 2) * 2
            self.children[idx].insert(point)
        else:
            if point in self.points:
                return
            self.points.append(point)
            if len(self.points) > QuadNode.SPLIT_THRESHOLD:
                self.split()

    def split(self) -> None:
        '''
        Split the quad node into 4 children
        '''
        w = self.w // 2
        h = self.h // 2
        self.children = [
            QuadNode(w, h, self.id + [0], self.x, self.y, self),
            QuadNode(self.w - w, h, self.id + [1], self.x + w, self.y, self),
            QuadNode(w, self.h - h, self.id + [2], self.x, self.y + h, self),
            QuadNode(self.w - w, self.h - h, self.id + [3], self.x + w, self.y + h, self),
        ]
        for p in self.points:
            self.insert(p)
        self.points = []

    def get_containing_node(self, point: Point) -> 'QuadNode':
        '''
        Get the cell that contains the point
        '''
        if self.has_children():
            idx = int(point.x >= self.x + self.w // 2) + int(point.y >= self.y + self.h // 2) * 2
            return self.children[idx].get_containing_node(point)
        else:
            return self

    def to_dict(self):
        '''
        Convert the quad tree to a dictionary
        '''
        if self.has_children():
            return {str(c.id[-1]): c.to_dict() for c in self.children}
        else:
            return self.points

    def overlap(self, other: 'QuadNode') -> bool:
        '''
        Check if two quad nodes overlap
        '''
        return not (
            self.x + self.w < other.x or
            other.x + other.w < self.x or
            self.y + self.h < other.y or
            other.y + other.h < self.y
        )

    def search_range(self, x: int, y: int, half_w):
        return self._search_range(QuadNode(half_w * 2, half_w * 2, [], x - half_w, y - half_w))

    def _search_range(self, node: 'QuadNode'):
        '''
        Search for points within a range with generator
        '''
        if not self.overlap(node):
            return
        if self.has_children():
            for c in self.children:
                yield from c._search_range(node)
        else:
            for p in self.points:
                if node.x <= p.x and node.x + node.w > p.x and node.y <= p.y and node.y + node.h > p.y:
                    yield p


class QuadTreeVisualizer(QuadNode):
    def __init__(self, w: int, h: int) -> None:
        super().__init__(w, h, [0,], 0, 0, None)
        pygame.init()

        self.bk_color = (255, 255, 255)
        self.line_color = (0, 0, 0)
        self.point_color = (0, 0, 0)
        self.highlight_color = (255, 0, 0)
        self.point_radius = 2

        self.draw_lines = True

        self.base_map = pygame.Surface((w, h))

        self.side_width = 300

        self.font = pygame.font.Font('freesansbold.ttf', 32)

        # drawing
        self.search_time = 0

    def visualize(self):
        '''
        Visualize the quad tree
        '''
        screen = pygame.display.set_mode((self.w + self.side_width, self.h))
        self.base_map.fill(self.bk_color)
        self._visualize(self.base_map)

        screen.fill((255, 255, 255))
        screen.blit(self.base_map, (0, 0))
        screen.blit(self.font.render('search time:', True, (0, 0, 0)), (self.w + 10, 10))

        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    screen.fill((255, 255, 255))
                    screen.blit(self.base_map, (0, 0))

                    half_dimension = 30
                    mouse_p = pygame.mouse.get_pos()
                    t = time.time()
                    for p in self.search_range(mouse_p[0], mouse_p[1], half_dimension):
                        pygame.draw.circle(screen, self.highlight_color, (p.x, p.y), self.point_radius)
                    print(time.time() - t)

                    pygame.draw.circle(screen, self.highlight_color, pygame.mouse.get_pos(), self.point_radius, 1)

                    screen.blit(self.font.render('search time:', True, (0, 0, 0)), (self.w + 10, 10))
                    screen.blit(self.font.render(f'{round((time.time() - t)*1000, 3)}ms', True, (0, 0, 0)), (self.w + 10, 60))

                    pygame.display.flip()

    def _visualize(self, screen: pygame.Surface):
        '''
        Visualize the quad tree
        '''
        nodes = [self]

        for node in nodes:
            if node.has_children():
                for c in node.children:
                    nodes.append(c)
                if self.draw_lines:
                    pygame.draw.line(screen, self.line_color, (node.x + node.w // 2, node.y), (node.x + node.w // 2, node.y + node.h))
                    pygame.draw.line(screen, self.line_color, (node.x, node.y + node.h // 2), (node.x + node.w, node.y + node.h // 2))
            else:
                for p in node.points:
                    pygame.draw.circle(screen, self.point_color, (p.x, p.y), self.point_radius)


def uneven_rand():
    ratio = 2
    return (math.pow(math.e, random.random() * ratio) - 1) / (math.pow(math.e, ratio) - 1)


def main():
    w = 800
    h = 800
    q = QuadTreeVisualizer(w, h)

    for i in range(10000):
        # q.insert(Point(random.randint(0, w - 1), random.randint(0, h - 1)))
        q.insert(Point(
            int(uneven_rand() * w),
            int((1 - uneven_rand()) * h),
        ))

    # pprint(q.to_dict())

    # print(q.get_containing_cell(Point(700, 1)))

    q.draw_lines = False
    q.visualize()


if __name__ == "__main__":
    main()
